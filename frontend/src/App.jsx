import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

const suggestions = [
  'What is the return policy?',
  'What is the status of order ORD-10066?',
  'Can I still return order ORD-10066?',
  'What is the loyalty level of customer CUST-1019?',
]

function App() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  async function sendMessage(text = question) {
    const userQuestion = text.trim()

    if (!userQuestion || loading) return

    setMessages((previous) => [
      ...previous,
      {
        role: 'user',
        content: userQuestion,
      },
    ])

    setQuestion('')
    setLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userQuestion,
        }),
      })

      if (!response.ok) {
        throw new Error(`Request failed: HTTP ${response.status}`)
      }

      const data = await response.json()

      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content: data.answer,
          route: data.route,
          generationMode: data.generation_mode,
          sources: data.sources || [],
        },
      ])
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content: `Unable to complete the request: ${error.message}`,
          error: true,
          sources: [],
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    sendMessage()
  }

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>✦ Enterprise AI Assistant</h1>
          <p>
            Your enterprise assistant for orders, customer information,
            warranties and company policies.
          </p>
          <p>
            Fictional enterprise data · Reference date: 30 September 2026
          </p>
        </div>
        <span className="status-badge">LIVE DEMO</span>
      </header>

      <main className="chat-container">
        {messages.length === 0 && (
          <section className="welcome">
            <h2>How can I help you today?</h2>
            <p>Choose a suggested question or write your own.</p>

            <div className="suggestions">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  disabled={loading}
                  onClick={() => sendMessage(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </section>
        )}

        <section className="messages" aria-live="polite">
          {messages.map((message, index) => (
            <article
              key={index}
              className={`message ${message.role}`}
            >
              <div className="message-role">
                {message.role === 'user' ? 'You' : 'AI Assistant'}
              </div>

              <div className="message-content">
                {message.role === 'assistant' ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    skipHtml
                  >
                    {message.content}
                  </ReactMarkdown>
                ) : (
                  <p>{message.content}</p>
                )}
              </div>

              {(message.route || message.generationMode) && (
                <div className="message-metadata">
                  {message.route && (
                    <div className="message-route">
                      Route: <strong>{message.route}</strong>
                    </div>
                  )}

                  {message.generationMode && (
                    <div className="message-generation">
                      Generation: <strong>
                        {{
                          llm: 'OpenAI',
                          deterministic: 'Python',
                          local_fallback: 'Local fallback',
                        }[message.generationMode] || 'Unknown'}
                      </strong>
                    </div>
                  )}
                </div>
              )}

              {message.sources?.length > 0 && (
                <div className="message-sources">
                  <strong>Sources</strong>
                  <ul>
                    {message.sources.map((source, sourceIndex) => (
                      <li key={`${source}-${sourceIndex}`}>
                        {source}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </article>
          ))}

          {loading && (
            <div className="message assistant">
              <div className="message-role">AI Assistant</div>
              <div className="message-content">
                <p>Thinking...</p>
              </div>
            </div>
          )}
        </section>
      </main>

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about orders, customers or company policies..."
          maxLength={1000}
          disabled={loading}
          aria-label="Your question"
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? 'Thinking...' : 'Send'}
        </button>
      </form>
    </div>
  )
}

export default App
