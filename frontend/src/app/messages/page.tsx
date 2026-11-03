import Header from '@/components/Header';

export default function MessagesPage() {
  return (
    <>
      <Header pendingApprovals={3} />
      
      <main
        style={{
          maxWidth: 'var(--max-width-wide)',
          margin: '0 auto',
          padding: 'var(--spacing-page)',
        }}
      >
        {/* Page Header */}
        <section style={{ marginBottom: 'var(--spacing-3xl)' }}>
          <h1
            style={{
              fontSize: 'var(--font-size-h1)',
              fontWeight: 'var(--font-weight-semibold)',
              marginBottom: 'var(--spacing-sm)',
            }}
          >
            Messages
          </h1>
          <p
            style={{
              fontSize: 'var(--font-size-body)',
              color: 'var(--color-text-secondary)',
            }}
          >
            Chat with your customers
          </p>
        </section>

        {/* Messages Layout */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '350px 1fr',
            gap: 'var(--spacing-2xl)',
            height: 'calc(100vh - 200px)',
          }}
        >
          {/* Conversations List */}
          <div
            className="card"
            style={{
              padding: 0,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Search */}
            <div style={{ padding: 'var(--spacing-lg)', borderBottom: '1px solid var(--color-border)' }}>
              <input
                type="text"
                placeholder="Search conversations..."
                style={{
                  width: '100%',
                  height: 'var(--input-height)',
                  padding: 'var(--input-padding)',
                  borderRadius: 'var(--radius-input)',
                  border: '1px solid var(--color-border-input)',
                  fontSize: 'var(--font-size-body)',
                }}
              />
            </div>

            {/* Conversations */}
            <div style={{ flex: 1, overflowY: 'auto' }}>
              <ConversationItem
                name="Priya Sharma"
                message="Hi, is this saree available in blue color?"
                time="5m ago"
                unread={2}
                active
              />
              <ConversationItem
                name="Rajesh Kumar"
                message="What's the delivery time?"
                time="1h ago"
                unread={1}
              />
              <ConversationItem
                name="Anita Patel"
                message="Thank you so much! Received the order."
                time="2h ago"
                unread={0}
              />
              <ConversationItem
                name="Deepak Singh"
                message="Can you provide bulk discount?"
                time="5h ago"
                unread={0}
              />
              <ConversationItem
                name="Meena Reddy"
                message="Product quality is excellent!"
                time="1d ago"
                unread={0}
              />
            </div>
          </div>

          {/* Chat Area */}
          <div
            className="card"
            style={{
              padding: 0,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Chat Header */}
            <div
              style={{
                padding: 'var(--spacing-lg)',
                borderBottom: '1px solid var(--color-border)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-md)',
              }}
            >
              <div
                style={{
                  width: 'var(--avatar-size)',
                  height: 'var(--avatar-size)',
                  borderRadius: '50%',
                  background: 'var(--color-primary-light)',
                  color: 'var(--color-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '16px',
                  fontWeight: 'var(--font-weight-semibold)',
                }}
              >
                P
              </div>
              <div>
                <div style={{ fontWeight: 'var(--font-weight-semibold)', fontSize: 'var(--font-size-body)' }}>
                  Priya Sharma
                </div>
                <div style={{ fontSize: 'var(--font-size-small)', color: 'var(--color-text-muted)' }}>
                  Active now
                </div>
              </div>
            </div>

            {/* Messages */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: 'var(--spacing-2xl)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--spacing-lg)',
              }}
            >
              <CustomerMessage
                message="Hi, is this saree available in blue color?"
                time="10:30 AM"
              />
              <SellerMessage
                message="Hello! Yes, we have it in blue. Would you like to see photos?"
                time="10:32 AM"
              />
              <CustomerMessage
                message="Yes please! Also, what's the price?"
                time="10:33 AM"
              />
              <SellerMessage
                message="It's ₹8,500. I'll send you the photos right away."
                time="10:35 AM"
              />
            </div>

            {/* Message Input */}
            <div
              style={{
                padding: 'var(--spacing-lg)',
                borderTop: '1px solid var(--color-border)',
                display: 'flex',
                gap: 'var(--spacing-md)',
              }}
            >
              <input
                type="text"
                placeholder="Type your message..."
                style={{
                  flex: 1,
                  height: 'var(--input-height)',
                  padding: 'var(--input-padding)',
                  borderRadius: 'var(--radius-input)',
                  border: '1px solid var(--color-border-input)',
                  fontSize: 'var(--font-size-body)',
                }}
              />
              <button
                className="btn-primary"
                style={{
                  height: 'var(--button-height)',
                  padding: '0 24px',
                }}
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}

interface ConversationItemProps {
  name: string;
  message: string;
  time: string;
  unread: number;
  active?: boolean;
}

function ConversationItem({ name, message, time, unread, active = false }: ConversationItemProps) {
  return (
    <div
      style={{
        padding: 'var(--spacing-lg)',
        borderBottom: '1px solid var(--color-border)',
        background: active ? 'var(--color-primary-light)' : 'transparent',
        cursor: 'pointer',
        transition: 'var(--transition)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--spacing-xs)' }}>
        <div style={{ fontWeight: 'var(--font-weight-semibold)', fontSize: 'var(--font-size-body)' }}>
          {name}
        </div>
        <div style={{ fontSize: 'var(--font-size-small)', color: 'var(--color-text-muted)' }}>
          {time}
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div
          style={{
            fontSize: 'var(--font-size-small)',
            color: 'var(--color-text-secondary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            flex: 1,
          }}
        >
          {message}
        </div>
        {unread > 0 && (
          <span
            style={{
              marginLeft: 'var(--spacing-sm)',
              minWidth: '20px',
              height: '20px',
              padding: '0 6px',
              borderRadius: '10px',
              background: 'var(--color-primary)',
              color: 'white',
              fontSize: '12px',
              fontWeight: 'var(--font-weight-bold)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {unread}
          </span>
        )}
      </div>
    </div>
  );
}

interface MessageProps {
  message: string;
  time: string;
}

function CustomerMessage({ message, time }: MessageProps) {
  return (
    <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
      <div style={{ maxWidth: '70%' }}>
        <div
          style={{
            padding: 'var(--spacing-md) var(--spacing-lg)',
            borderRadius: 'var(--radius-lg)',
            background: 'var(--color-bg-hover)',
            fontSize: 'var(--font-size-body)',
          }}
        >
          {message}
        </div>
        <div
          style={{
            fontSize: 'var(--font-size-tiny)',
            color: 'var(--color-text-muted)',
            marginTop: 'var(--spacing-xs)',
            paddingLeft: 'var(--spacing-lg)',
          }}
        >
          {time}
        </div>
      </div>
    </div>
  );
}

function SellerMessage({ message, time }: MessageProps) {
  return (
    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
      <div style={{ maxWidth: '70%' }}>
        <div
          style={{
            padding: 'var(--spacing-md) var(--spacing-lg)',
            borderRadius: 'var(--radius-lg)',
            background: 'var(--color-primary)',
            color: 'white',
            fontSize: 'var(--font-size-body)',
          }}
        >
          {message}
        </div>
        <div
          style={{
            fontSize: 'var(--font-size-tiny)',
            color: 'var(--color-text-muted)',
            marginTop: 'var(--spacing-xs)',
            paddingRight: 'var(--spacing-lg)',
            textAlign: 'right',
          }}
        >
          {time}
        </div>
      </div>
    </div>
  );
}
