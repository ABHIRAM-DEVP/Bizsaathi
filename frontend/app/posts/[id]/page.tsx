import Link from "next/link";
import { SellerShell } from "../../components/SellerShell";

export const instant = false;

export default async function PostDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <SellerShell><Link className="back-link" href="/">← Home</Link><section className="page-heading"><div><h1>Create a post</h1><p>Product facts first. Every claim is checked before it reaches your approval queue.</p></div><span className="chip chip-good">Mock assistant</span></section><section className="post-studio"><article className="surface-card"><span className="chip">Post draft · {id}</span><div className="studio-image"></div><label className="studio-label">Caption<textarea defaultValue="Festive season ke liye perfect ✨ Handwoven Chanderi dupatta in marigold, with a soft gold zari border. Light, graceful, made to be worn." /></label><p className="studio-hashtags">#Chanderi #Handwoven #FestiveWear #SupportSmallBusiness</p><div className="button-row"><button className="button button-primary">Check claims</button><button className="button button-secondary">Save draft</button></div></article><aside className="surface-card"><h2>Checked before it reaches you</h2><ul className="check-list"><li>✓ Every fact links to your catalogue</li><li>✓ No personal details in the post</li><li>✓ No misleading offer or price</li></ul><div className="review-warning"><b>Unverified claim</b><p>“Best quality in India” has no evidence. It will stay blocked until removed or confirmed.</p></div><Link className="button button-secondary full-button" href="/trace/demo">View verification trace</Link></aside></section></SellerShell>;
}
