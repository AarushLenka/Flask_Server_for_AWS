package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
)

const (
	supabaseURL = "https://ioxmssaxiqqvhqowrxwi.supabase.co"
	tableName   = "Data"
)

var supabaseAPIKey string

func main() {
	supabaseAPIKey = os.Getenv("SUPABASE_API_KEY")
	
	http.HandleFunc("/", receiveHandler)
	
	port := os.Getenv("PORT")
	if port == "" {
		port = "5000"
	}
	
	log.Printf("Server starting on port %s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}

func receiveHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		handleGet(w, r)
	case http.MethodPost:
		handlePost(w, r)
	default:
		w.WriteHeader(http.StatusBadRequest)
	}
}

func handleGet(w http.ResponseWriter, r *http.Request) {
	// AWS confirmation
	token := r.URL.Query().Get("confirmationToken")
	if token != "" {
		log.Printf("✅ Received AWS confirmation token: %s", token)
		w.WriteHeader(http.StatusOK)
		return
	}
	
	w.WriteHeader(http.StatusBadRequest)
}

func handlePost(w http.ResponseWriter, r *http.Request) {
	// Read IoT message
	body, err := io.ReadAll(r.Body)
	if err != nil {
		log.Printf("❌ Error reading body: %v", err)
		sendError(w, err)
		return
	}
	defer r.Body.Close()
	
	var data map[string]interface{}
	if err := json.Unmarshal(body, &data); err != nil {
		log.Printf("❌ Error parsing JSON: %v", err)
		sendError(w, err)
		return
	}
	
	log.Printf("📩 Raw IoT payload: %v", data)
	
	// Extract actual data (inside 'message')
	var payload interface{}
	if message, ok := data["message"]; ok {
		payload = message
	} else {
		payload = data
	}
	
	log.Printf("📦 Cleaned payload to send: %v", payload)
	
	// Send to Supabase
	status, err := sendToSupabase(payload)
	if err != nil {
		log.Printf("❌ Error: %v", err)
		sendError(w, err)
		return
	}
	
	response := map[string]interface{}{
		"status":          "ok",
		"supabase_status": status,
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func sendToSupabase(payload interface{}) (int, error) {
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return 0, err
	}
	
	url := fmt.Sprintf("%s/rest/v1/%s", supabaseURL, tableName)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return 0, err
	}
	
	req.Header.Set("apikey", supabaseAPIKey)
	req.Header.Set("Authorization", "Bearer "+supabaseAPIKey)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Prefer", "return=representation")
	
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	
	respBody, _ := io.ReadAll(resp.Body)
	log.Printf("➡️ Supabase response: %d %s", resp.StatusCode, string(respBody))
	
	return resp.StatusCode, nil
}

func sendError(w http.ResponseWriter, err error) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusInternalServerError)
	json.NewEncoder(w).Encode(map[string]string{
		"error": err.Error(),
	})
}
