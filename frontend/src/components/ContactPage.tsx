import React, { useState } from 'react';
import { ArrowLeft, Mail, MessageSquare, Send, CheckCircle2, HelpCircle, Clock } from 'lucide-react';

interface ContactPageProps {
  onBackToStudio: () => void;
  onNavigate: (route: string) => void;
}

export const ContactPage: React.FC<ContactPageProps> = ({ onBackToStudio, onNavigate }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('general');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Mailto fallback or local confirmation
    const mailtoUrl = `mailto:madushankamax8@gmail.com?subject=[Kokoro Studio] ${encodeURIComponent(subject)}: ${encodeURIComponent(name)}&body=${encodeURIComponent(`From: ${name} (${email})\n\n${message}`)}`;
    window.open(mailtoUrl, '_blank');
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-12">
        {/* Top Navigation */}
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-6">
          <button
            onClick={onBackToStudio}
            className="inline-flex items-center gap-2 text-sm font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Voice Studio</span>
          </button>
          <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
            <button onClick={() => onNavigate('guide')} className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Guide</button>
            <span>•</span>
            <button onClick={() => onNavigate('voices')} className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Voices</button>
            <span>•</span>
            <button onClick={() => onNavigate('about')} className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">About</button>
          </div>
        </div>

        {/* Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-semibold border border-blue-200 dark:border-blue-800">
            <Mail className="w-3.5 h-3.5 text-blue-500" />
            <span>Developer Support &amp; Feedback</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight">
            Contact &amp; Support
          </h1>
          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Have questions about Kokoro Voice Studio, audio mastering features, commercial licensing, or API integration? We are here to help.
          </p>
        </div>

        {/* Contact Info & Form Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* Info Card (5 cols) */}
          <div className="md:col-span-5 space-y-6">
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-blue-500" />
                <span>Direct Contact Channels</span>
              </h2>
              
              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-slate-400 block mb-0.5">Primary Support Email</span>
                  <a
                    href="mailto:madushankamax8@gmail.com"
                    className="font-semibold text-blue-600 dark:text-blue-400 hover:underline text-sm"
                  >
                    madushankamax8@gmail.com
                  </a>
                </div>

                <div>
                  <span className="text-slate-400 block mb-0.5">Response Time Expectation</span>
                  <p className="text-slate-600 dark:text-slate-300 flex items-center gap-1.5 font-medium">
                    <Clock className="w-3.5 h-3.5 text-emerald-500" />
                    <span>Within 24 to 48 business hours</span>
                  </p>
                </div>

                <div>
                  <span className="text-slate-400 block mb-0.5">Open Source Repository</span>
                  <a
                    href="https://github.com/dilshan916/kokoro-voice-studio"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-semibold text-slate-800 dark:text-slate-200 hover:text-blue-600 dark:hover:text-blue-400 underline"
                  >
                    github.com/dilshan916/kokoro-voice-studio
                  </a>
                </div>

                <div>
                  <span className="text-slate-400 block mb-0.5">Physical Operating Region</span>
                  <p className="text-slate-600 dark:text-slate-300">
                    Online Cloud Service • Cloudflare Global Anycast Edge Network
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Tips */}
            <div className="p-6 rounded-3xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/60 shadow-sm space-y-3">
              <h3 className="text-sm font-bold text-blue-900 dark:text-blue-200 flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span>Common Inquiries</span>
              </h3>
              <ul className="text-xs text-blue-800 dark:text-blue-300/90 space-y-2 list-disc list-inside">
                <li>Commercial use of synthesized audio is 100% permitted under Apache 2.0.</li>
                <li>Anonymous free tier includes 30,000 characters every 30 days.</li>
                <li>Unlimited Pro status can be unlocked via the Studio pricing modal.</li>
              </ul>
            </div>
          </div>

          {/* Form Card (7 cols) */}
          <div className="md:col-span-7">
            <div className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                Send a Message or Report an Issue
              </h2>

              {submitted ? (
                <div className="p-6 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-center space-y-3">
                  <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
                  <h3 className="font-bold text-emerald-900 dark:text-emerald-200 text-base">Message Ready!</h3>
                  <p className="text-xs text-emerald-700 dark:text-emerald-300 max-w-md mx-auto leading-relaxed">
                    Your email client has been opened to dispatch your inquiry directly to our engineering mailbox. We typically respond within 24–48 hours.
                  </p>
                  <button
                    onClick={() => setSubmitted(false)}
                    className="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 transition-colors"
                  >
                    Send Another Message
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Your Name / Organization
                    </label>
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Alex Rivera"
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Your Email Address
                    </label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@example.com"
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Subject / Topic
                    </label>
                    <select
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
                    >
                      <option value="general">General Inquiry &amp; Feedback</option>
                      <option value="bug">Bug Report / Audio Synthesis Glitch</option>
                      <option value="commercial">Commercial Licensing &amp; Enterprise</option>
                      <option value="api">Developer API Key &amp; Quota</option>
                      <option value="billing">Billing &amp; VIP Code Support</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Message Details
                    </label>
                    <textarea
                      required
                      rows={5}
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Describe your question or the steps to reproduce any issue you encountered..."
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow-md transition-colors"
                  >
                    <Send className="w-4 h-4" />
                    <span>Send Message to Support</span>
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
