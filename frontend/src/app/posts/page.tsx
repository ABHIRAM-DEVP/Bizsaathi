import Header from '@/components/Header';
import Link from 'next/link';

export default function PostsPage() {
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
        {/* Page Header */}
        <section
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 'var(--spacing-3xl)',
          }}
        >
          <div>
            <h1
              style={{
                fontSize: 'var(--font-size-h1)',
                fontWeight: 'var(--font-weight-semibold)',
                marginBottom: 'var(--spacing-sm)',
              }}
            >
              Posts
            </h1>
            <p
              style={{
                fontSize: 'var(--font-size-body)',
                color: 'var(--color-text-secondary)',
              }}
            >
              Share updates with your customers
            </p>
          </div>
          <Link
            href="/posts/new"
            className="btn-primary"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              height: 'var(--button-height)',
              padding: 'var(--button-padding)',
              borderRadius: 'var(--radius-button)',
              fontSize: 'var(--font-size-body)',
              fontWeight: 'var(--font-weight-medium)',
              textDecoration: 'none',
            }}
          >
            + Create Post
          </Link>
        </section>

        {/* Filter Tabs */}
        <section style={{ marginBottom: 'var(--spacing-2xl)' }}>
          <div
            style={{
              display: 'flex',
              gap: 'var(--spacing-md)',
              borderBottom: '2px solid var(--color-border)',
              paddingBottom: '0',
            }}
          >
            <TabButton label="All Posts" count={12} active />
            <TabButton label="Published" count={8} />
            <TabButton label="Pending Approval" count={3} />
            <TabButton label="Drafts" count={1} />
          </div>
        </section>

        {/* Posts List */}
        <section
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--spacing-lg)',
          }}
        >
          <PostCard
            title="Summer Collection Launch 🌻"
            content="Excited to announce our brand new summer collection featuring handwoven cotton sarees in vibrant colors! Limited stock available."
            status="published"
            publishedAt="2 hours ago"
            engagement={{ likes: 45, comments: 8, shares: 12 }}
          />
          <PostCard
            title="Festival Sale - 20% Off"
            content="Special festival discount on all products! Use code FESTIVAL20 at checkout. Valid until..."
            status="pending"
            createdAt="5 hours ago"
          />
          <PostCard
            title="Behind the Scenes: Our Weaving Process"
            content="Take a look at how we create our beautiful handloom textiles. Each piece takes 3-4 days of skilled work..."
            status="published"
            publishedAt="1 day ago"
            engagement={{ likes: 128, comments: 23, shares: 45 }}
          />
          <PostCard
            title="Customer Testimonial"
            content="Thank you Mrs. Sharma for your wonderful review! We're thrilled that you loved your purchase."
            status="published"
            publishedAt="2 days ago"
            engagement={{ likes: 67, comments: 12, shares: 8 }}
          />
        </section>
      </main>
    </>
  );
}

interface TabButtonProps {
  label: string;
  count: number;
  active?: boolean;
}

function TabButton({ label, count, active = false }: TabButtonProps) {
  return (
    <button
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-sm)',
        padding: 'var(--spacing-md) var(--spacing-lg)',
        background: 'transparent',
        border: 'none',
        borderBottom: active ? '2px solid var(--color-primary)' : '2px solid transparent',
        fontSize: 'var(--font-size-body)',
        fontWeight: 'var(--font-weight-medium)',
        color: active ? 'var(--color-primary)' : 'var(--color-text-secondary)',
        cursor: 'pointer',
        marginBottom: '-2px',
        transition: 'var(--transition)',
      }}
    >
      {label}
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          minWidth: '20px',
          height: '20px',
          padding: '0 6px',
          borderRadius: '10px',
          background: active ? 'var(--color-primary-light)' : 'var(--color-bg-hover)',
          color: active ? 'var(--color-primary)' : 'var(--color-text-muted)',
          fontSize: '12px',
          fontWeight: 'var(--font-weight-semibold)',
        }}
      >
        {count}
      </span>
    </button>
  );
}

interface PostCardProps {
  title: string;
  content: string;
  status: 'published' | 'pending' | 'draft';
  publishedAt?: string;
  createdAt?: string;
  engagement?: {
    likes: number;
    comments: number;
    shares: number;
  };
}

function PostCard({ title, content, status, publishedAt, createdAt, engagement }: PostCardProps) {
  const getStatusBadge = () => {
    switch (status) {
      case 'published':
        return <span className="badge-green">Published</span>;
      case 'pending':
        return <span className="badge-orange">Pending Approval</span>;
      case 'draft':
        return <span className="badge-gray">Draft</span>;
      default:
        return null;
    }
  };

  return (
    <div
      className="card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--spacing-lg)',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 'var(--spacing-lg)',
        }}
      >
        <div style={{ flex: 1 }}>
          <h3
            style={{
              fontSize: 'var(--font-size-h4)',
              fontWeight: 'var(--font-weight-semibold)',
              marginBottom: 'var(--spacing-xs)',
            }}
          >
            {title}
          </h3>
          <div
            style={{
              fontSize: 'var(--font-size-small)',
              color: 'var(--color-text-muted)',
            }}
          >
            {publishedAt && `Published ${publishedAt}`}
            {createdAt && `Created ${createdAt}`}
          </div>
        </div>
        {getStatusBadge()}
      </div>

      {/* Content */}
      <p
        style={{
          fontSize: 'var(--font-size-body)',
          color: 'var(--color-text-secondary)',
          lineHeight: 'var(--line-height-relaxed)',
        }}
      >
        {content}
      </p>

      {/* Footer with Engagement Stats */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: 'var(--spacing-lg)',
          borderTop: '1px solid var(--color-border)',
        }}
      >
        {engagement && (
          <div
            style={{
              display: 'flex',
              gap: 'var(--spacing-xl)',
              fontSize: 'var(--font-size-small)',
              color: 'var(--color-text-muted)',
            }}
          >
            <span>❤️ {engagement.likes}</span>
            <span>💬 {engagement.comments}</span>
            <span>🔗 {engagement.shares}</span>
          </div>
        )}
        <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
          <button
            className="btn-secondary"
            style={{
              height: '36px',
              padding: '0 16px',
              fontSize: 'var(--font-size-small)',
            }}
          >
            Edit
          </button>
          <button
            className="btn-outline"
            style={{
              height: '36px',
              padding: '0 16px',
              fontSize: 'var(--font-size-small)',
            }}
          >
            View
          </button>
        </div>
      </div>
    </div>
  );
}
