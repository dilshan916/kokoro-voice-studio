import React, { useState } from 'react';
import {
  X,
  Sparkles,
  Check,
  Key,
  Zap,
  CreditCard,
  Loader2,
  ShieldCheck,
  ToggleLeft,
  ToggleRight,
  Info,
} from 'lucide-react';
import { UserQuota } from '../types';
import { kokoroApi } from '../api/kokoroApi';

interface PricingModalProps {
  isOpen: boolean;
  onClose: () => void;
  quota: UserQuota | null;
  onQuotaUpdated: () => void;
}

export const PricingModal: React.FC<PricingModalProps> = ({
  isOpen,
  onClose,
  quota,
  onQuotaUpdated,
}) => {
  const [promoCode, setPromoCode] = useState('');
  const [isRedeeming, setIsRedeeming] = useState(false);
  const [redeemResult, setRedeemResult] = useState<{ success: boolean; message: string } | null>(null);

  // Checkout & Subscription States
  const [upgradeNotice, setUpgradeNotice] = useState<string | null>(null);
  const [isUpdatingRenewal, setIsUpdatingRenewal] = useState(false);
  const [subscriptionNotice, setSubscriptionNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  if (!isOpen) return null;

  const isPro = quota?.tier === 'pro';
  const usage = quota?.monthly_usage || 0;
  const limit = quota?.monthly_limit || 30000;
  const usagePercent = limit > 0 ? Math.min(100, Math.round((usage / limit) * 100)) : 0;

  const formatExpiryDate = (isoStr?: string) => {
    if (!isoStr) return null;
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return null;
      return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return null;
    }
  };

  const handleRedeem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promoCode.trim() || isRedeeming) return;

    setIsRedeeming(true);
    setRedeemResult(null);

    try {
      const res = await kokoroApi.redeemLicense(promoCode);
      setRedeemResult({
        success: res.success,
        message: res.message,
      });
      if (res.success) {
        setPromoCode('');
        onQuotaUpdated();
      }
    } catch (err: any) {
      setRedeemResult({
        success: false,
        message: err.response?.data?.detail || 'Failed to redeem code. Please try again.',
      });
    } finally {
      setIsRedeeming(false);
    }
  };

  const handleStripeCheckout = () => {
    setUpgradeNotice(
      "Pro upgrades are temporarily unavailable. Please check back soon!"
    );
  };

  const handleToggleAutoRenew = async () => {
    if (isUpdatingRenewal) return;
    setIsUpdatingRenewal(true);
    setSubscriptionNotice(null);

    const nextState = !quota?.cancel_at_period_end;
    try {
      const res = await kokoroApi.toggleAutoRenew(nextState);
      setSubscriptionNotice({ type: 'success', message: res.message });
      onQuotaUpdated();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to update auto-renewal setting.';
      setSubscriptionNotice({ type: 'error', message: msg });
    } finally {
      setIsUpdatingRenewal(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/60 dark:bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-in fade-in duration-150 select-none"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-3xl p-5 sm:p-6 shadow-2xl space-y-4 max-h-[92vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3.5 border-b border-slate-100 dark:border-slate-700/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-500 via-indigo-600 to-blue-600 text-white flex items-center justify-center font-bold shadow-md shadow-indigo-500/20 shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white">
                  Quota &amp; Subscriptions
                </h2>
                {isPro && (
                  <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-extrabold uppercase border border-emerald-500/25">
                    PRO ACTIVE
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Manage your character quota, Pro subscription, and VIP licenses
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-700/60 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 hover:text-slate-800 dark:text-slate-300 dark:hover:text-white flex items-center justify-center transition-colors cursor-pointer shrink-0"
            aria-label="Close modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Current Quota Card */}
        <div className="bg-slate-50/80 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700/80 rounded-2xl p-4 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Current Billing Cycle Usage
            </span>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400 font-mono">
              Cycle: {quota?.billing_cycle_month || 'Current Month'}
            </span>
          </div>

          <div className="flex items-baseline justify-between">
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight font-mono">
                {usage.toLocaleString()}
              </span>
              <span className="text-xs font-semibold text-slate-400">
                / {isPro ? '∞ Unlimited' : `${limit.toLocaleString()} chars`}
              </span>
            </div>
            <span className={`text-xs font-bold ${isPro ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-300'}`}>
              {isPro ? '✨ 100% Unlimited' : `${usagePercent}% used`}
            </span>
          </div>

          {!isPro && (
            <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
              <div
                className={`h-full transition-all duration-500 rounded-full ${
                  usagePercent > 90
                    ? 'bg-rose-500'
                    : usagePercent > 70
                    ? 'bg-amber-500'
                    : 'bg-gradient-to-r from-blue-500 to-indigo-500'
                }`}
                style={{ width: `${usagePercent}%` }}
              />
            </div>
          )}

          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            {isPro
              ? '✨ You have unlimited speech generation enabled on this device.'
              : 'Free quota resets automatically on the 1st of every month (UTC).'}
          </p>
        </div>

        {/* Plan Comparison Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          {/* Free Tier Card */}
          <div className="p-4 sm:p-4.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/80 flex flex-col justify-between space-y-3.5 shadow-xs">
            <div className="space-y-2.5">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">Free Tier</span>
                <div className="flex items-baseline gap-1 mt-0.5">
                  <span className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">$0</span>
                  <span className="text-xs font-medium text-slate-400">/ forever</span>
                </div>
              </div>
              <ul className="space-y-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-500 shrink-0" strokeWidth={2.5} />
                  <span>30,000 characters / month</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-500 shrink-0" strokeWidth={2.5} />
                  <span>All 60 Neural AI voices</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-500 shrink-0" strokeWidth={2.5} />
                  <span>Studio EQ &amp; Subtitle export</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-emerald-500 shrink-0" strokeWidth={2.5} />
                  <span>Zero login required</span>
                </li>
              </ul>
            </div>

            <div className="pt-1">
              <div
                className={`w-full py-2 px-3 rounded-xl text-xs font-semibold text-center ${
                  !isPro
                    ? 'bg-slate-100 dark:bg-slate-700/60 text-slate-700 dark:text-slate-200 font-bold border border-slate-200/80 dark:border-slate-600/80'
                    : 'bg-slate-100/60 dark:bg-slate-700/30 text-slate-400 dark:text-slate-500'
                }`}
              >
                {!isPro ? 'Current Plan' : 'Standard Tier'}
              </div>
            </div>
          </div>

          {/* Pro Tier Card (Real Stripe Checkout) */}
          <div className="p-4 sm:p-4.5 rounded-2xl border-2 border-blue-500 bg-gradient-to-b from-blue-50/60 to-indigo-50/40 dark:from-blue-950/25 dark:to-indigo-950/25 flex flex-col justify-between space-y-3.5 relative shadow-sm">
            <span className="absolute -top-2.5 right-3.5 text-[10px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xs">
              Recommended
            </span>

            <div className="space-y-2.5">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 fill-current text-blue-600 dark:text-blue-400" />
                  Pro Unlimited
                </span>
                <div className="flex items-baseline gap-1 mt-0.5">
                  <span className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">$9.99</span>
                  <span className="text-xs font-medium text-slate-400">/ month</span>
                </div>
              </div>
              <ul className="space-y-2 text-xs font-medium text-slate-700 dark:text-slate-200">
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" strokeWidth={2.5} />
                  <span>Unlimited characters</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" strokeWidth={2.5} />
                  <span>High-priority queue</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" strokeWidth={2.5} />
                  <span>Commercial audio license</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" strokeWidth={2.5} />
                  <span>Developer API access</span>
                </li>
              </ul>
            </div>

            <div className="pt-1">
              <div
                className={`w-full py-2 px-3 rounded-xl text-xs font-bold text-center flex items-center justify-center gap-1.5 ${
                  isPro
                    ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 dark:text-emerald-300'
                    : 'bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400'
                }`}
              >
                {isPro ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-500" strokeWidth={2.5} />
                    <span>Active Plan</span>
                  </>
                ) : (
                  'Pro Tier'
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Upgrade / Subscription Action Block */}
        <div className="space-y-2">
          {isPro ? (
            <div className="space-y-2.5">
              {/* Auto-Renewal Management Panel */}
              <div className="p-3.5 sm:p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700/80 space-y-2.5 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                    Subscription Status:
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1.5 ${
                      quota?.cancel_at_period_end
                        ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                        : 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${quota?.cancel_at_period_end ? 'bg-amber-500' : 'bg-emerald-500 animate-pulse'}`} />
                    {quota?.cancel_at_period_end
                      ? `Cancelled (Active until ${formatExpiryDate(quota?.subscription_expires_at) || 'Period End'})`
                      : `Active (Renews ${formatExpiryDate(quota?.subscription_expires_at) || 'Monthly'})`}
                  </span>
                </div>

                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  {quota?.cancel_at_period_end
                    ? `Auto-renewal is turned off. You retain 100% full Pro Unlimited access until ${formatExpiryDate(quota?.subscription_expires_at) || 'the end of your 30-day period'}. No further payments will be charged.`
                    : `Your subscription renews automatically each month at $9.99 on ${formatExpiryDate(quota?.subscription_expires_at) || 'your billing date'}. You can cancel anytime with one click and retain full access for your remaining days.`}
                </p>

                <button
                  type="button"
                  onClick={handleToggleAutoRenew}
                  disabled={isUpdatingRenewal}
                  className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60 ${
                    quota?.cancel_at_period_end
                      ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-xs'
                      : 'bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700'
                  }`}
                >
                  {isUpdatingRenewal ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Updating...</span>
                    </>
                  ) : quota?.cancel_at_period_end ? (
                    <>
                      <ToggleRight className="w-4 h-4 text-white" strokeWidth={2.2} />
                      <span>Turn Auto-Renewal Back ON</span>
                    </>
                  ) : (
                    <>
                      <ToggleLeft className="w-4 h-4 text-amber-500" strokeWidth={2.2} />
                      <span>Cancel Subscription (Turn OFF Auto-Renewal)</span>
                    </>
                  )}
                </button>
              </div>

              {subscriptionNotice && (
                <div
                  className={`p-2.5 rounded-xl text-xs flex items-center justify-between animate-in fade-in duration-150 ${
                    subscriptionNotice.type === 'success'
                      ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                      : 'bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400'
                  }`}
                >
                  <span>{subscriptionNotice.message}</span>
                  <button
                    type="button"
                    onClick={() => setSubscriptionNotice(null)}
                    className="text-slate-400 hover:text-slate-600 font-bold px-1.5"
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {upgradeNotice && (
                <div className="p-3.5 rounded-2xl bg-blue-500/10 dark:bg-blue-500/15 border border-blue-500/30 text-blue-700 dark:text-blue-300 text-xs flex items-start justify-between gap-2.5 animate-in fade-in duration-150 shadow-xs">
                  <div className="flex items-start gap-2.5">
                    <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                    <div className="space-y-0.5">
                      <span className="font-bold">Notice</span>
                      <p className="text-[11px] text-blue-600/90 dark:text-blue-400/90 leading-relaxed">
                        {upgradeNotice}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setUpgradeNotice(null)}
                    className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 font-bold px-1"
                  >
                    ✕
                  </button>
                </div>
              )}

              <button
                type="button"
                onClick={handleStripeCheckout}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-600 hover:from-blue-500 hover:to-indigo-500 text-white text-sm font-bold shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <CreditCard className="w-4 h-4" strokeWidth={2.2} />
                <span>Upgrade to Pro ($9.99/mo)</span>
              </button>

              <div className="flex items-center justify-center gap-1.5 text-xs text-slate-400 dark:text-slate-500">
                <ShieldCheck className="w-4 h-4 text-emerald-500" strokeWidth={2.2} />
                <span>256-Bit SSL Encrypted • Cancel anytime</span>
              </div>
            </div>
          )}
        </div>

        {/* Promo / VIP Key Redemption */}
        <div className="pt-3.5 border-t border-slate-100 dark:border-slate-700/60 space-y-2.5">
          <div className="flex items-center gap-2">
            <Key className="w-3.5 h-3.5 text-amber-500" strokeWidth={2.2} />
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
              Have a Promo Code or VIP License Key?
            </span>
          </div>

          <form onSubmit={handleRedeem} className="flex gap-2">
            <input
              type="text"
              placeholder="e.g. KOKORO-VIP-FRIEND"
              value={promoCode}
              onChange={(e) => setPromoCode(e.target.value)}
              className="flex-1 h-9 text-xs font-mono uppercase bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-3 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={isRedeeming || !promoCode.trim()}
              className="h-9 px-4 bg-slate-900 dark:bg-white hover:bg-slate-800 dark:hover:bg-slate-100 disabled:opacity-40 text-white dark:text-slate-900 text-xs font-bold rounded-xl transition-colors shrink-0 flex items-center gap-1.5 cursor-pointer"
            >
              {isRedeeming ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                'Redeem Key'
              )}
            </button>
          </form>

          {redeemResult && (
            <div
              className={`p-3 rounded-xl text-xs flex items-center justify-between animate-in fade-in duration-150 ${
                redeemResult.success
                  ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                  : 'bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400'
              }`}
            >
              <span>{redeemResult.message}</span>
              <button
                onClick={() => setRedeemResult(null)}
                className="text-slate-400 hover:text-slate-600 font-bold px-1.5"
              >
                ✕
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PricingModal;
