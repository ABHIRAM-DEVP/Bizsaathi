import Header from '@/components/Header';
import Link from 'next/link';

export default function ProductsPage() {
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
              My Products
            </h1>
            <p
              style={{
                fontSize: 'var(--font-size-body)',
                color: 'var(--color-text-secondary)',
              }}
            >
              Manage your product catalog
            </p>
          </div>
          <Link
            href="/products/new"
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
            + Add Product
          </Link>
        </section>

        {/* Filter Bar */}
        <section
          style={{
            display: 'flex',
            gap: 'var(--spacing-md)',
            marginBottom: 'var(--spacing-2xl)',
          }}
        >
          <select
            style={{
              height: 'var(--input-height)',
              padding: 'var(--input-padding)',
              borderRadius: 'var(--radius-input)',
              border: '1px solid var(--color-border-input)',
              fontSize: 'var(--font-size-body)',
              color: 'var(--color-text)',
              background: 'white',
              cursor: 'pointer',
            }}
          >
            <option>All Categories</option>
            <option>Sarees</option>
            <option>Dupattas</option>
            <option>Fabrics</option>
          </select>
          <select
            style={{
              height: 'var(--input-height)',
              padding: 'var(--input-padding)',
              borderRadius: 'var(--radius-input)',
              border: '1px solid var(--color-border-input)',
              fontSize: 'var(--font-size-body)',
              color: 'var(--color-text)',
              background: 'white',
              cursor: 'pointer',
            }}
          >
            <option>All Stock Status</option>
            <option>In Stock</option>
            <option>Low Stock</option>
            <option>Out of Stock</option>
          </select>
        </section>

        {/* Products Grid */}
        <section
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: 'var(--spacing-2xl)',
          }}
        >
          <ProductCard
            name="Handwoven Banarasi Saree - Red"
            price="₹8,500"
            stock="In Stock"
            stockCount={12}
            category="Sarees"
            image="🌺"
          />
          <ProductCard
            name="Cotton Dupattas - Blue Set"
            price="₹1,200"
            stock="In Stock"
            stockCount={25}
            category="Dupattas"
            image="💙"
          />
          <ProductCard
            name="Silk Fabric - Gold Border"
            price="₹4,800"
            stock="Low Stock"
            stockCount={3}
            category="Fabrics"
            image="✨"
          />
          <ProductCard
            name="Traditional Saree - Green"
            price="₹6,200"
            stock="In Stock"
            stockCount={8}
            category="Sarees"
            image="💚"
          />
          <ProductCard
            name="Handloom Cotton Saree - Yellow"
            price="₹3,500"
            stock="Out of Stock"
            stockCount={0}
            category="Sarees"
            image="🌻"
          />
          <ProductCard
            name="Designer Dupatta - Pink"
            price="₹1,800"
            stock="In Stock"
            stockCount={15}
            category="Dupattas"
            image="🌸"
          />
        </section>
      </main>
    </>
  );
}

interface ProductCardProps {
  name: string;
  price: string;
  stock: 'In Stock' | 'Low Stock' | 'Out of Stock';
  stockCount: number;
  category: string;
  image: string;
}

function ProductCard({ name, price, stock, stockCount, category, image }: ProductCardProps) {
  const getStockBadge = () => {
    switch (stock) {
      case 'In Stock':
        return <span className="badge-green">{stock}</span>;
      case 'Low Stock':
        return <span className="badge-orange">{stock}</span>;
      case 'Out of Stock':
        return <span className="badge-red">{stock}</span>;
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
        padding: '0',
        overflow: 'hidden',
      }}
    >
      {/* Product Image */}
      <div
        style={{
          width: '100%',
          height: '200px',
          background: 'linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-primary-lighter) 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '64px',
        }}
      >
        {image}
      </div>

      {/* Product Info */}
      <div
        style={{
          padding: 'var(--spacing-lg)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--spacing-md)',
        }}
      >
        {/* Category Badge */}
        <span
          className="badge-gray"
          style={{
            alignSelf: 'flex-start',
            fontSize: '12px',
          }}
        >
          {category}
        </span>

        {/* Name */}
        <h3
          style={{
            fontSize: 'var(--font-size-h4)',
            fontWeight: 'var(--font-weight-semibold)',
            lineHeight: 'var(--line-height-tight)',
          }}
        >
          {name}
        </h3>

        {/* Price and Stock */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div
            style={{
              fontSize: 'var(--font-size-h4)',
              fontWeight: 'var(--font-weight-semibold)',
              color: 'var(--color-primary)',
            }}
          >
            {price}
          </div>
          {getStockBadge()}
        </div>

        {/* Stock Count */}
        <div
          style={{
            fontSize: 'var(--font-size-small)',
            color: 'var(--color-text-muted)',
          }}
        >
          {stockCount} units available
        </div>

        {/* Actions */}
        <div
          style={{
            display: 'flex',
            gap: 'var(--spacing-sm)',
            paddingTop: 'var(--spacing-md)',
            borderTop: '1px solid var(--color-border)',
          }}
        >
          <button
            className="btn-secondary"
            style={{
              flex: 1,
              height: '36px',
              fontSize: 'var(--font-size-small)',
            }}
          >
            Edit
          </button>
          <button
            className="btn-outline"
            style={{
              flex: 1,
              height: '36px',
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
