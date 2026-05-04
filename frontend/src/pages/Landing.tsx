import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mic, Video, MessageSquare, ArrowRight, Activity, Sparkles } from 'lucide-react';
import { Button } from '../components/UI/Button';
import { useAuthStore } from '../store/useAuthStore';

// Landing Navigation
const LandingNav = () => {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuthStore();

    return (
        <nav className="absolute top-0 w-full z-50 px-6 py-5 flex justify-between items-center max-w-7xl mx-auto left-0 right-0">
            <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-teal-500/20 flex items-center justify-center">
                    <Activity size={18} className="text-teal-400" />
                </div>
                <span className="text-xl font-serif text-slate-100 font-medium tracking-wide">MindSculpt AI</span>
            </div>

            <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
                <a href="#how-it-works" onClick={(e) => { e.preventDefault(); document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' }); }} className="hover:text-teal-400 transition-colors cursor-pointer">How it Works</a>
                <a href="#features" onClick={(e) => { e.preventDefault(); document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' }); }} className="hover:text-teal-400 transition-colors cursor-pointer">Features</a>
                <a href="#about" onClick={(e) => { e.preventDefault(); document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' }); }} className="hover:text-teal-400 transition-colors cursor-pointer">About</a>
            </div>

            <div className="flex items-center gap-4">
                {isAuthenticated ? (
                    <Button onClick={() => navigate('/dashboard')} size="sm" variant="primary">
                        Go to Dashboard
                    </Button>
                ) : (
                    <>
                        <Link to="/login" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                            Sign In
                        </Link>
                        <Button onClick={() => navigate('/register')} size="sm" variant="primary">
                            Get Started
                        </Button>
                    </>
                )}
            </div>
        </nav>
    );
};

// Hero Section
const Hero = () => {
    const navigate = useNavigate();

    return (
        <div className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
            {/* Abstract Background */}
            <div className="absolute inset-0 z-0">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-[100px]" />
                <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-violet-600/10 rounded-full blur-[120px]" />
                <div className="absolute inset-0 bg-[url('/grid-pattern.svg')] opacity-[0.03]" />
            </div>

            <div className="container px-4 mx-auto relative z-10 text-center max-w-4xl">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                >
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-teal-400 text-xs font-medium uppercase tracking-wider mb-6">
                        <Sparkles size={12} />
                        <span>AI-Powered Emotional Intelligence</span>
                    </div>

                    <h1 className="text-5xl md:text-7xl font-serif text-slate-100 mb-6 leading-tight">
                        An AI That Understands <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-violet-400">
                            How You Feel
                        </span>
                    </h1>

                    <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
                        Real-time emotion recognition from your voice, face, and words —
                        creating meaningful, empathetic conversations that help you understand yourself better.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <Button onClick={() => navigate('/register')} size="lg" className="w-full sm:w-auto hover:scale-105 transition-transform">
                            Get Started Free <ArrowRight size={18} />
                        </Button>
                        <Button onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })} variant="outline" size="lg" className="w-full sm:w-auto">
                            See How It Works
                        </Button>
                    </div>
                </motion.div>

                {/* Floating UI Elements Mockup */}
                <motion.div
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4, duration: 0.8 }}
                    className="mt-16 mx-auto max-w-3xl glass-panel p-2 rounded-2xl border border-white/10 shadow-2xl overflow-hidden"
                >
                    <div className="bg-[#0f1115] rounded-xl overflow-hidden aspect-[16/9] relative flex items-center justify-center">
                        {/* Mock Interface Content */}
                        <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-[#0f1115] to-transparent z-10" />

                        <div className="flex gap-4 items-end mb-8 relative z-0">
                            <div className="w-12 h-12 rounded-full bg-slate-700 animate-pulse" />
                            <div className="w-64 h-16 rounded-2xl rounded-bl-sm bg-slate-800" />
                        </div>

                        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex gap-4">
                            <div className="w-12 h-12 rounded-full bg-red-500/20 border border-red-500/50 flex items-center justify-center animate-pulse">
                                <div className="w-3 h-3 bg-red-500 rounded-full" />
                            </div>
                            <div className="h-12 px-6 rounded-full bg-slate-800 border border-white/10 flex items-center text-slate-400 text-sm">
                                Listening...
                            </div>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

// Features Section
const Features = () => {
    return (
        <section id="features" className="py-24 bg-[#0a0c10] relative">
            <div className="container mx-auto px-6">
                <div className="text-center mb-16">
                    <h2 className="text-3xl font-serif text-slate-100 mb-4">Multimodal Intelligence</h2>
                    <p className="text-slate-400 max-w-2xl mx-auto">
                        MindSculpt AI captures nuances that text-only AIs miss by analyzing three distinct layers of communication simultaneously.
                    </p>
                </div>

                <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                    {[
                        {
                            icon: <Mic className="w-8 h-8 text-teal-400" />,
                            title: "Voice Analysis",
                            desc: "Detects tone, pitch, and rhythm to understand emotional intensity beyond just words."
                        },
                        {
                            icon: <Video className="w-8 h-8 text-violet-400" />,
                            title: "Facial Expression",
                            desc: "Real-time micro-expression analysis captures fleeting emotions like surprise or hidden distress."
                        },
                        {
                            icon: <MessageSquare className="w-8 h-8 text-blue-400" />,
                            title: "Linguistic Sentiment",
                            desc: "Deep text analysis identifies cognitive patterns and underlying sentiment in your speech."
                        }
                    ].map((feature, i) => (
                        <div key={i} className="glass-panel p-8 rounded-2xl hover:border-white/20 transition-colors group">
                            <div className="mb-6 w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center group-hover:bg-white/10 transition-colors">
                                {feature.icon}
                            </div>
                            <h3 className="text-xl font-semibold text-slate-100 mb-3">{feature.title}</h3>
                            <p className="text-slate-400 leading-relaxed">{feature.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

// How it Works Section
const HowItWorks = () => {
    const steps = [
        {
            num: '01',
            title: 'Start a Session',
            desc: 'Open the chat and begin speaking naturally. MindSculpt AI activates your microphone and camera to capture your voice and facial expressions in real-time.'
        },
        {
            num: '02',
            title: 'Multimodal Analysis',
            desc: 'Our AI simultaneously analyzes your audio tone, facial micro-expressions, and linguistic patterns using three specialized neural models.'
        },
        {
            num: '03',
            title: 'Empathetic Response',
            desc: 'MindSculpt AI synthesizes the emotion signals and generates a deeply personalized, context-aware response that reflects your current emotional state.'
        },
        {
            num: '04',
            title: 'Track Your Journey',
            desc: 'Review session histories, emotion timelines, and personality insights on your dashboard to understand your emotional patterns over time.'
        }
    ];

    return (
        <section id="how-it-works" className="py-24 bg-[#0D1B2A] relative">
            <div className="absolute inset-0 bg-gradient-to-b from-[#0a0c10] to-[#0D1B2A]" />
            <div className="container mx-auto px-6 relative z-10">
                <div className="text-center mb-16">
                    <h2 className="text-3xl font-serif text-slate-100 mb-4">How It Works</h2>
                    <p className="text-slate-400 max-w-2xl mx-auto">
                        From your first word to actionable emotional insights — here's the MindSculpt AI pipeline.
                    </p>
                </div>

                <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-8">
                    {steps.map((step, i) => (
                        <div key={i} className="glass-panel p-8 rounded-2xl border border-white/10 hover:border-teal-500/30 transition-colors group">
                            <div className="text-5xl font-bold text-teal-500/20 group-hover:text-teal-500/30 transition-colors mb-4 font-serif">{step.num}</div>
                            <h3 className="text-xl font-semibold text-slate-100 mb-3">{step.title}</h3>
                            <p className="text-slate-400 leading-relaxed">{step.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

// About Section
const About = () => {
    return (
        <section id="about" className="py-24 bg-[#0a0c10] relative">
            <div className="container mx-auto px-6">
                <div className="max-w-4xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-serif text-slate-100 mb-4">About MindSculpt AI</h2>
                        <p className="text-slate-400 max-w-2xl mx-auto">
                            Built with empathy at its core.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-12 items-center">
                        <div className="space-y-6">
                            <p className="text-slate-300 leading-relaxed">
                                MindSculpt AI is an AI research project
                                that bridges the gap between human emotion and machine understanding.
                            </p>
                            <p className="text-slate-400 leading-relaxed">
                                By combining state-of-the-art models for audio, visual, and linguistic analysis,
                                MindSculpt AI creates conversations that feel genuinely understood — not just heard.
                            </p>
                            <p className="text-slate-400 leading-relaxed">
                                Built with a privacy-first approach, your emotional data is processed securely
                                and you retain full control over what's stored and shared.
                            </p>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            {[
                                { label: 'Emotion Classes', value: '8' },
                                { label: 'Modal Streams', value: '3' },
                                { label: 'Response Time', value: '<2s' },
                                { label: 'Privacy First', value: '✓' },
                            ].map((stat, i) => (
                                <div key={i} className="glass-panel p-6 rounded-xl border border-white/10 text-center">
                                    <div className="text-3xl font-bold text-teal-400 mb-1">{stat.value}</div>
                                    <div className="text-xs text-slate-500 uppercase tracking-wider">{stat.label}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

// Footer
const Footer = () => {
    return (
        <footer className="bg-[#050608] border-t border-white/5 py-12">
            <div className="container mx-auto px-6 text-center">
                <div className="flex items-center justify-center gap-2 mb-8">
                    <Activity size={24} className="text-teal-500 opacity-80" />
                    <span className="text-2xl font-serif text-slate-200">MindSculpt AI</span>
                </div>

                <div className="flex flex-wrap justify-center gap-8 text-slate-400 mb-8 text-sm">
                    <a href="#" className="hover:text-teal-400">Privacy Policy</a>
                    <a href="#" className="hover:text-teal-400">Terms of Service</a>
                    <a href="#" className="hover:text-teal-400">Ethics Statement</a>
                    <a href="#" className="hover:text-teal-400">Contact Us</a>
                </div>

                <p className="text-xs text-slate-600">
                    © {new Date().getFullYear()} MindSculpt AI. All rights reserved.<br />
                    Designed for empathy, built with privacy.
                </p>
            </div>
        </footer>
    );
};

export const Landing = () => {
    return (
        <div className="bg-[#0D1B2A] text-slate-200 min-h-screen">
            <LandingNav />
            <Hero />
            <Features />
            <HowItWorks />
            <About />

            {/* CTA Section */}
            <section className="py-24 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-b from-[#0a0c10] to-[#0D1B2A]" />
                <div className="container mx-auto px-6 relative z-10 text-center">
                    <h2 className="text-4xl font-serif text-white mb-6">Ready to be understood?</h2>
                    <p className="text-slate-400 mb-8 max-w-xl mx-auto">
                        Join thousands of users who are discovering deeper self-awareness through empathetic AI conversation.
                    </p>
                    <Button size="lg" onClick={() => window.location.href = '/register'}>
                        Create your Free Account
                    </Button>
                </div>
            </section>

            <Footer />
        </div>
    );
};
