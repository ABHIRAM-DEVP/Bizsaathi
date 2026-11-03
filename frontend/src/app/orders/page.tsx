import Header from '@/components/Header';

export default function OrdersPage() {
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
        <section style={{ marginBottom: 'var(--spacing-3xl)' }}>
          <h1
            style={{
              fontSize: 'var(--font-size-h1)',
              fontWeight: 'var(--font-weight-semibold)',
              marginBottom: 'var(--spacing-sm)',
            }}
          >
            Orders
          </h1>
          <p
            style={{
              fontSize: 'var(--font-size-body)',
              color: 'var(--color-text-secondary)',
            }}
          >
            Manage customer orders and fulfillment
          </p>
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
            <TabButton label="All Orders" count={45} active />
            <TabButton label="Pending" count={8} />
            <TabButton label="Processing" count={12} />
            <TabButton label="Shipped" count={18} />
            <TabButton label="Delivered" count={7} />
          </div>
        </section>

        {/* Orders Table */}
        <section className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table>
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Products</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <OrderRow
                orderId="#1234"
                customer="Priya Sharma"
                products="Banarasi Saree - Red"
                amount="₹8,500"
                status="pending"
                date="2 hours ago"
              />
              <OrderRow
                orderId="#1233"
                customer="Rajesh Kumar"
                products="Cotton Dupatta Set (x2)"
                amount="₹2,400"
                status="processing"
                date="5 hours ago"
              />
              <OrderRow
                orderId="#1232"
                customer="Anita Patel"
                products="Silk Fabric - Gold Border"
                amount="₹4,800"
                status="shipped"
                date="1 day ago"
              />
              <OrderRow
                orderId="#1231"
                customer="Deepak Singh"
                products="Traditional Saree - Green"
                amount="₹6,200"
                status="shipped"
                date="1 day ago"
              />
              <OrderRow
                orderId="#1230"
                customer="Meena Reddy"
                products="Handloom Cotton Saree"
                amount="₹3,500"
                status="delivered"
                date="3 days ago"
              />
              <OrderRow
                orderId="#1229"
                customer="Vijay Malhotra"
                products="Designer Dupatta - Pink"
                amount="₹1,800"
                status="delivered"
                date="4 days ago"
              />
            </tbody>
          </table>
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

interface OrderRowProps {
  orderId: string;
  customer: string;
  products: string;
  amount: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  date: string;
}

function OrderRow({ orderId, customer, products, amount, status, date }: OrderRowProps) {
  const getStatusBadge = () => {
    switch (status) {
      case 'pending':
        return <span className="badge-orange">Pending</span>;
      case 'processing':
        return <span className="badge" style={{ background: 'var(--color-info-bg)', color: 'var(--color-info)' }}>Processing</span>;
      case 'shipped':
        return <span className="badge" style={{ background: 'var(--color-info-bg)', color: 'var(--color-info)' }}>Shipped</span>;
      case 'delivered':
        return <span className="badge-green">Delivered</span>;
      case 'cancelled':
        return <span className="badge-red">Cancelled</span>;
      default:
        return <span className="badge-gray">{status}</span>;
    }
  };

  return (
    <tr>
      <td>
        <span style={{ fontWeight: 'var(--font-weight-medium)', fontFamily: 'monospace' }}>
          {orderId}
        </span>
      </td>
      <td>{customer}</td>
      <td style={{ color: 'var(--color-text-secondary)' }}>{products}</td>
      <td>
        <span style={{ fontWeight: 'var(--font-weight-semibold)' }}>
          {amount}
        </span>
      </td>
      <td>{getStatusBadge()}</td>
      <td style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-small)' }}>
        {date}
      </td>
      <td>
        <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
          <button
            className="btn-secondary"
            style={{
              height: '32px',
              padding: '0 12px',
              fontSize: 'var(--font-size-small)',
            }}
          >
            View
          </button>
          <button
            className="btn-outline"
            style={{
              height: '32px',
              padding: '0 12px',
              fontSize: 'var(--font-size-small)',
            }}
          >
            Update
          </button>
        </div>
      </td>
    </tr>
  );
}
