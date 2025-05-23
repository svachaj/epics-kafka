package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
	"github.com/segmentio/kafka-go"
)

// Subscribe represents the incoming WebSocket message requesting PV subscriptions.
type Subscribe struct {
	Type string   `json:"type"`
	PVs  []string `json:"pvs"`
}

// PVMessage is the schema broadcast back to WebSocket clients.
type PVMessage struct {
	Type      string      `json:"type"` // always "pv"
	Name      string      `json:"name"`
	Value     interface{} `json:"value"`
	Severity  int         `json:"severity"`
	OK        bool        `json:"ok"`
	Timestamp float64     `json:"timestamp"`
	Units     string      `json:"units"`
}

var (
	// Allow any origin; tighten for production.
	upgrader = websocket.Upgrader{CheckOrigin: func(r *http.Request) bool { return true }}
	// Kafka bootstrap servers (comma‑separated list)
	kafkaBrokers = func() []string {
		bootstrap := os.Getenv("KAFKA_BOOTSTRAP_SERVERS")
		if bootstrap == "" {
			bootstrap = "localhost:9092"
		}
		return strings.Split(bootstrap, ",")
	}()
)

func wsHandler(c echo.Context) error {
	conn, err := upgrader.Upgrade(c.Response(), c.Request(), nil)
	if err != nil {
		return err
	}
	defer conn.Close()

	// Context to cancel Kafka readers when socket closes.
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Track all running reader goroutines per connection.
	var wg sync.WaitGroup

	// Channel for serializing WebSocket writes
	writeChan := make(chan []byte)
	wg.Add(1)
	go func() {
		defer wg.Done()
		for msg := range writeChan {
			if err := conn.WriteMessage(websocket.TextMessage, msg); err != nil {
				log.Println("WebSocket write error:", err)
				return
			}
		}
	}()

	for {
		// Await a subscribe message from the client.
		_, raw, err := conn.ReadMessage()
		if err != nil {
			log.Println("WebSocket read error:", err)
			break
		}
		var sub Subscribe
		if err := json.Unmarshal(raw, &sub); err != nil || sub.Type != "subscribe" {
			log.Println("invalid subscribe payload")
			continue
		}

		// Spin up a Kafka reader per requested PV (topic).
		for _, pv := range sub.PVs {
			topic := pv // capture loop var
			wg.Add(1)
			go func() {
				defer wg.Done()
				reader := kafka.NewReader(kafka.ReaderConfig{
					Brokers:  kafkaBrokers,
					GroupID:  "gateway-" + topic + "-" + time.Now().Format("150405.000"),
					Topic:    topic,
					MinBytes: 1,
					MaxBytes: 10e6,
				})
				defer reader.Close()

				for {
					m, err := reader.ReadMessage(ctx)
					if err != nil {
						log.Println("Kafka read error:", err)
						return
					}

					// Expect EPICS bridge JSON payload; pass through with minimal transform.
					var src map[string]interface{}
					if err := json.Unmarshal(m.Value, &src); err != nil {
						continue // skip malformed
					}

					out := PVMessage{
						Type:      "pv",
						Name:      topic,
						Value:     src["value"],
						Severity:  int(coerceFloat(src["severity"])),
						OK:        coerceBool(src["ok"]),
						Timestamp: coerceFloat(src["timestamp"]),
						Units:     coerceString(src["units"]),
					}
					b, _ := json.Marshal(out)

					// Send the message to the writer goroutine
					select {
					case writeChan <- b:
					case <-ctx.Done():
						return
					}
				}
			}()
		}
	}

	// socket closed: stop all readers and writer
	cancel()
	close(writeChan)
	wg.Wait()
	return nil
}

// coerce helpers – tolerant of absent/mismatched types.
func coerceFloat(v interface{}) float64 {
	switch t := v.(type) {
	case float64:
		return t
	case int64:
		return float64(t)
	case int:
		return float64(t)
	default:
		return 0
	}
}

func coerceBool(v interface{}) bool {
	switch t := v.(type) {
	case bool:
		return t
	default:
		return true // assume OK if missing
	}
}

// coerceString returns a string or empty if nil.
func coerceString(v interface{}) string {
	switch t := v.(type) {
	case string:
		return t
	case nil:
		return ""
	default:
		return ""
	}
}

func main() {
	// log brokers
	log.Println("Kafka brokers:", kafkaBrokers)
	e := echo.New()
	e.Use(middleware.Logger())
	e.Use(middleware.Recover())
	e.GET("/ws/pvs", wsHandler)
	addr := ":8080"
	log.Println("Gateway listening on", addr)
	e.Logger.Fatal(e.Start(addr))
}
