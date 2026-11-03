'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

interface HeaderProps {
  pendingApprovals?: number;
}

export default function Header({ pendingApprovals = 3 }: HeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();

  return (
    <header
      style={{
        height: 'var(--header-height)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--spacing-page)',
        background: 'white',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      {/* Logo and Nav */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
        {/* Logo */}
        <Link
          href="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            fontWeight: 'var(--font-weight-semibold)',
            fontSize: '18px',
            color: 'var(--color-text)',
          }}
        >
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'var(--color-primary)',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '16px',
              fontWeight: 'var(--font-weight-bold)',
            }}
          >
            B
          </div>
          BizSaathi
        </Link>

        {/* Navigation */}
        <nav style={{ display: 'flex', gap: '4px' }}>
          <NavLink href="/" label="Home" active={pathname === '/'} />
          <NavLink href="/posts" label="Posts" active={pathname === '/posts'} />
          <NavLink href="/products" label="Products" active={pathname === '/products'} />
          <NavLink href="/messages" label="Messages" active={pathname === '/messages'} />
          <NavLink href="/orders" label="Orders" active={pathname === '/orders'} />
        </nav>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Approvals Button */}
        <Link
          href="/approvals"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            height: 'var(--button-height)',
            padding: 'var(--button-padding)',
            borderRadius: 'var(--radius-button)',
            background: 'white',
            border: '1px solid var(--color-border)',
            fontSize: 'var(--font-size-body)',
            fontWeight: 'var(--font-weight-medium)',
            color: 'var(--color-text)',
            transition: 'var(--transition)',
            textDecoration: 'none',
          }}
        >
          Approvals
          {pendingApprovals > 0 && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                minWidth: '20px',
                height: '20px',
                padding: '0 6px',
                borderRadius: '10px',
                background: 'var(--color-warning)',
                color: 'white',
                fontSize: '12px',
                fontWeight: 'var(--font-weight-bold)',
              }}
            >
              {pendingApprovals}
            </span>
          )}
        </Link>

        {/* User Menu */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Account menu"
            aria-haspopup="true"
            aria-expanded={menuOpen}
            style={{
              width: 'var(--avatar-size)',
              height: 'var(--avatar-size)',
              borderRadius: '50%',
              border: 'none',
              background: 'var(--color-primary-light)',
              color: 'var(--color-primary)',
              fontSize: '16px',
              fontWeight: 'var(--font-weight-semibold)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            M
          </button>

          {menuOpen && (
            <div
              role="menu"
              style={{
                position: 'absolute',
                right: 0,
                top: 'calc(var(--avatar-size) + 8px)',
                minWidth: '240px',
                background: 'white',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-card)',
                boxShadow: 'var(--shadow-lg)',
                padding: '8px',
                zIndex: 50,
              }}
            >
              <div
                style={{
                  padding: '12px',
                  borderBottom: '1px solid var(--color-border)',
                  marginBottom: '4px',
                }}
              >
                <div style={{ fontSize: '14px', fontWeight: 'var(--font-weight-semibold)' }}>
                  Meera&apos;s Handlooms
                </div>
                <div
                  style={{
                    fontSize: '13px',
                    color: 'var(--color-success)',
                    fontWeight: 'var(--font-weight-medium)',
                    marginTop: '4px',
                  }}
                >
                  ✓ Verified Seller
                </div>
              </div>
              <MenuLink href="/trust" label="Trust and safety" />
              <MenuLink href="/channels" label="How customers reach you" />
              <MenuLink href="/models" label="Model settings" />
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

interface NavLinkProps {
  href: string;
  label: string;
  active?: boolean;
}

function NavLink({ href, label, active = false }: NavLinkProps) {
  return (
    <Link
      href={href}
      style={{
        display: 'flex',
        alignItems: 'center',
        height: 'var(--nav-item-height)',
        padding: 'var(--nav-item-padding)',
        borderRadius: 'var(--radius-md)',
        fontSize: 'var(--font-size-body)',
        fontWeight: 'var(--font-weight-medium)',
        color: active ? 'var(--color-primary)' : 'var(--color-text-secondary)',
        background: active ? 'var(--color-primary-light)' : 'transparent',
        transition: 'var(--transition-fast)',
        textDecoration: 'none',
      }}
    >
      {label}
    </Link>
  );
}

function MenuLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      role="menuitem"
      style={{
        display: 'flex',
        alignItems: 'center',
        height: 'var(--nav-item-height)',
        padding: 'var(--nav-item-padding)',
        borderRadius: 'var(--radius-md)',
        fontSize: '14px',
        fontWeight: 'var(--font-weight-medium)',
        color: 'var(--color-text)',
        textDecoration: 'none',
        transition: 'var(--transition-fast)',
      }}
    >
      {label}
    </Link>
  );
}
