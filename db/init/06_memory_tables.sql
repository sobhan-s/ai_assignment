-- Create a new schema for conversation memory so it doesn't mix with the business data
CREATE SCHEMA IF NOT EXISTS memory;

-- Create the messages table to store chat history by thread_id
CREATE TABLE IF NOT EXISTS memory.messages (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an index on thread_id for fast retrieval
CREATE INDEX IF NOT EXISTS idx_memory_messages_thread_id ON memory.messages(thread_id);

-- Ensure genai_user has read/write access to the memory schema
GRANT USAGE ON SCHEMA memory TO genai_user;
GRANT ALL PRIVILEGES ON TABLE memory.messages TO genai_user;
GRANT USAGE, SELECT ON SEQUENCE memory.messages_id_seq TO genai_user;
