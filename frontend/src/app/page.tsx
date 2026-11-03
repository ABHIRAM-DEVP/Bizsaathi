import Header from '@/components/Header';

export default function HomePage() {
  return (
    <>
      <Header pendingApprovals={3} />
      
      <main
        style={{
          maxWidth: 'var(--max-width-content)',
          margin: '0 auto',
          padding: 'var(--spacing-page)',
        }}
      >
        {/* Welcome Section */}
        <section style={{ marginBottom: 'var(--spacing-3xl)' }}>
          <h1
            style={{
              fontSize: 'var(--font-size-h1)',
              fontWeight: 'var(--font-weight-semibold)',
              marginBottom: 'var(--spacing-md)',
            }}
          >
            Welcome back, Meera! 👋
          </h1>
          <p
            style={{
              fontSize: 'var(--font-size-body)',
              color: 'var(--color-text-secondary)',
            }}
          >
            Here&apos;s what&apos;s happening with your business today
          </p>
        </section>

        {/* Stats Cards */}
        <section
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 'var(--spacing-2xl)',
            marginBottom: 'var(--spacing-4xl)',
          }}
        >
          <StatCard
            title="Today's Orders"
            value="12"
            change="+8% from yesterday"
            trend="up"
          />
          <StatCard
            title="Revenue This Week"
            value="₹45,280"
            change="+12% from last week"
            trend="up"
          />
          <StatCard
            title="Active Products"
            value="28"
            change="2 need attention"
            trend="neutral"
          />
        </section>

        {/* Quick Actions */}
        <section style={{ marginBottom: 'var(--spacing-4xl)' }}>
          <h2
            style={{
              fontSize: 'var(--font-size-h3)',
              fontWeight: 'var(--font-weight-semibold)',
              marginBottom: 'var(--spacing-xl)',
            }}
          >
            Quick Actions
          </h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 'var(--spacing-lg)',
            }}
          >
            <ActionCard
              title="Create Post"
              description="Share updates with customers"
              icon="📝"
            />
            <ActionCard
              title="Add Product"
              description="List new items for sale"
              icon="📦"
            />
            <ActionCard
              title="Check Messages"
              description="3 unread conversations"
              icon="💬"
              badge="3"
            />
            <ActionCard
              title="View Analytics"
              description="See your performance"
              icon="📊"
            />
          </div>
        </section>

        {/* Recent Activity */}
        <section>
          <h2
            style={{
              fontSize: 'var(--font-size-h3)',
              fontWeight: 'var(--font-weight-semibold)',
              marginBottom: 'var(--spacing-xl)',
            }}
          >
            Recent Activity
          </h2>
          <div className="card">
            <ActivityItem
              type="order"
              message="New order #1234 from Priya Sharma"
              time="5 minutes ago"
            />
            <ActivityItem
              type="message"
              message="Message from Rajesh Kumar about product inquiry"
              time="1 hour ago"
            />
            <ActivityItem
              type="approval"
              message="Post about 'Summer Collection' needs approval"
              time="2 hours ago"
            />
            <ActivityItem
              type="product"
              message="Product 'Handwoven Saree - Blue' is low in stock"
              time="3 hours ago"
            />
          </div>
        </section>
      </main>
    </>
  );
}

interface StatCardProps {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
}

function StatCard({ title, value, change, trend }: StatCardProps) {
  return (
    <div className="card">
      <div
        style={{
          fontSize: 'var(--font-size-small)',
          color: 'var(--color-text-secondary)',
          marginBottom: 'var(--spacing-sm)',
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: '32px',
          fontWeight: 'var(--font-weight-semibold)',
          marginBottom: 'var(--spacing-sm)',
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: 'var(--font-size-small)',
          color:
            trend === 'up'
              ? 'var(--color-success)'
              : trend === 'down'
              ? 'var(--color-error)'
              : 'var(--color-text-muted)',
        }}
      >
        {change}
      </div>
    </div>
  );
}

interface ActionCardProps {
  title: string;
  description: string;
  icon: string;
  badge?: string;
}

function ActionCard({ title, description, icon, badge }: ActionCardProps) {
  return (
    <button
      className="card"
      style={{
        cursor: 'pointer',
        textAlign: 'left',
        position: 'relative',
        border: '1px solid var(--color-border)',
        background: 'white',
      }}
    >
      {badge && (
        <span
          className="badge-orange"
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            fontSize: '12px',
            padding: '2px 8px',
          }}
        >
          {badge}
        </span>
      )}
      <div
        style={{
          fontSize: '32px',
          marginBottom: 'var(--spacing-md)',
        }}
      >
        {icon}
      </div>
      <div
        style={{
          fontSize: 'var(--font-size-body)',
          fontWeight: 'var(--font-weight-semibold)',
          marginBottom: 'var(--spacing-xs)',
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: 'var(--font-size-small)',
          color: 'var(--color-text-secondary)',
        }}
      >
        {description}
      </div>
    </button>
  );
}

interface ActivityItemProps {
  type: 'order' | 'message' | 'approval' | 'product';
  message: string;
  time: string;
}

function ActivityItem({ type, message, time }: ActivityItemProps) {
  const getIcon = () => {
    switch (type) {
      case 'order':
        return '📦';
      case 'message':
        return '💬';
      case 'approval':
        return '✓';
      case 'product':
        return '⚠️';
      default:
        return '•';
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 'var(--spacing-md)',
        padding: 'var(--spacing-md) 0',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      <span style={{ fontSize: '20px' }}>{getIcon()}</span>
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontSize: 'var(--font-size-body)',
            marginBottom: 'var(--spacing-xs)',
          }}
        >
          {message}
        </div>
        <div
          style={{
            fontSize: 'var(--font-size-small)',
            color: 'var(--color-text-muted)',
          }}
        >
          {time}
        </div>
      </div>
    </div>
  );
}
