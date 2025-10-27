"use client"

import React, { useState, useEffect } from 'react';
import { ChevronDown, Users, MessageSquare, TrendingUp, Globe, DollarSign, Target, Award, Rocket } from 'lucide-react';

// Define the size type explicitly
type LogoSize = 'sm' | 'md' | 'lg';

interface LogoProps {
  size?: LogoSize;
  showText?: boolean;
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ size = "lg", showText = true, className = "" }) => {
  const iconSizes: Record<LogoSize, string> = {
    sm: "h-9 w-9 text-lg",
    md: "h-12 w-12 text-xl", 
    lg: "h-16 w-16 text-2xl"
  };
  
  const textSizes: Record<LogoSize, string> = {
    sm: "text-xl",
    md: "text-2xl",
    lg: "text-3xl"
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className={`relative rounded-xl bg-gradient-to-br from-[#1f7daf] to-[#104f73] grid place-items-center text-white font-bold shadow-lg ring-2 ring-[#1f7daf]/20 ${iconSizes[size]}`}>
        <span className="drop-shadow-sm">O</span>
      </div>
      {showText && (
        <span className={`font-semibold bg-gradient-to-r from-[#1f7daf] to-[#104f73] bg-clip-text text-transparent ${textSizes[size]}`}>
          Olaji
        </span>
      )}
    </div>
  );
};

interface SlideIndicatorProps {
  currentSlide: number;
  totalSlides: number;
  onSlideChange: (index: number) => void;
}

const SlideIndicator: React.FC<SlideIndicatorProps> = ({ currentSlide, totalSlides, onSlideChange }) => (
  <div className="fixed right-6 top-1/2 -translate-y-1/2 z-50 flex flex-col gap-2">
    {Array.from({ length: totalSlides }, (_, i) => (
      <button
        key={i}
        onClick={() => onSlideChange(i)}
        className={`w-3 h-3 rounded-full transition-all duration-300 ${
          i === currentSlide 
            ? 'bg-[#1f7daf] scale-125' 
            : 'bg-gray-300 hover:bg-gray-400'
        }`}
        aria-label={`Go to slide ${i + 1}`}
      />
    ))}
  </div>
);

interface SlideProps {
  children: React.ReactNode;
  className?: string;
  id: string;
}

const Slide: React.FC<SlideProps> = ({ children, className = "", id }) => (
  <section 
    id={id}
    className={`min-h-screen flex items-center justify-center px-4 py-16 ${className}`}
  >
    <div className="max-w-6xl mx-auto w-full">
      {children}
    </div>
  </section>
);

interface StatCardProps {
  number: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const StatCard: React.FC<StatCardProps> = ({ number, label, icon: Icon }) => (
  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 text-center">
    <Icon className="w-8 h-8 mx-auto mb-3 text-[#1f7daf]" />
    <div className="text-3xl font-bold text-[#1f7daf] mb-2">{number}</div>
    <div className="text-gray-600 dark:text-gray-300">{label}</div>
  </div>
);

interface FeatureCardProps {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ title, description, icon: Icon }) => (
  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
    <Icon className="w-10 h-10 text-[#1f7daf] mb-4" />
    <h3 className="text-xl font-semibold mb-3">{title}</h3>
    <p className="text-gray-600 dark:text-gray-300">{description}</p>
  </div>
);

export default function PitchDeck() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const totalSlides = 12;

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      const windowHeight = window.innerHeight;
      const newSlide = Math.floor(scrollPosition / windowHeight);
      setCurrentSlide(Math.min(newSlide, totalSlides - 1));
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSlide = (slideIndex: number) => {
    const slideElement = document.getElementById(`slide-${slideIndex}`);
    slideElement?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="font-['Plus_Jakarta_Sans'] bg-gradient-to-br from-gray-50 to-white dark:from-gray-950 dark:to-gray-900">
      <SlideIndicator 
        currentSlide={currentSlide} 
        totalSlides={totalSlides}
        onSlideChange={scrollToSlide}
      />

      {/* Slide 1: Cover */}
      <Slide id="slide-0" className="bg-gradient-to-br from-[#1f7daf]/5 to-[#104f73]/5">
        <div className="text-center">
          <Logo size="lg" className="justify-center mb-8" />
          <h1 className="text-6xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-[#1f7daf] to-[#104f73] bg-clip-text text-transparent">
            Olaji
          </h1>
          <p className="text-2xl md:text-3xl text-gray-600 dark:text-gray-300 mb-12 max-w-3xl mx-auto">
            School management, simplified through chat
          </p>
          <div className="flex justify-center">
            <ChevronDown className="w-8 h-8 text-[#1f7daf] animate-bounce" />
          </div>
        </div>
      </Slide>

      {/* Slide 2: Problem */}
      <Slide id="slide-1">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-5xl font-bold mb-8 text-gray-900 dark:text-white">The Problem</h2>
            <div className="space-y-6">
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border-l-4 border-red-500">
                <h3 className="text-xl font-semibold mb-2 text-red-600">Fragmented Systems</h3>
                <p className="text-gray-600 dark:text-gray-300">Schools struggle with disconnected tools for fees, attendance, and parent communication</p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border-l-4 border-orange-500">
                <h3 className="text-xl font-semibold mb-2 text-orange-600">Manual Processes</h3>
                <p className="text-gray-600 dark:text-gray-300">Time-consuming manual work leads to errors, delays, and poor engagement</p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border-l-4 border-yellow-500">
                <h3 className="text-xl font-semibold mb-2 text-yellow-600">Poor Transparency</h3>
                <p className="text-gray-600 dark:text-gray-300">Parents lack visibility into attendance, fees, and academic progress</p>
              </div>
            </div>
          </div>
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-red-500/20 to-orange-500/20 rounded-2xl blur-3xl"></div>
            <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
              <div className="text-4xl mb-4">😰</div>
              <p className="text-lg text-gray-600 dark:text-gray-300">
                "Managing our school feels like juggling a dozen different systems that don't talk to each other"
              </p>
              <p className="text-sm text-gray-500 mt-4">- School Administrator</p>
            </div>
          </div>
        </div>
      </Slide>

      {/* Slide 3: Solution */}
      <Slide id="slide-2" className="bg-gradient-to-br from-green-50/50 to-blue-50/50 dark:from-green-900/10 dark:to-blue-900/10">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold mb-8 text-gray-900 dark:text-white">Our Solution</h2>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 max-w-4xl mx-auto">
            <MessageSquare className="w-16 h-16 text-[#1f7daf] mx-auto mb-6" />
            <h3 className="text-3xl font-bold mb-4 text-[#1f7daf]">Chat-Based School Management</h3>
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
              Register schools, manage students, and process payments through simple chat commands
            </p>
          </div>
        </div>
        
        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard 
            icon={MessageSquare}
            title="Chat Interface"
            description="Intuitive chat commands make school management accessible to everyone"
          />
          <FeatureCard 
            icon={DollarSign}
            title="Embedded Payments"
            description="Seamless fee collection with M-Pesa and card integrations"
          />
          <FeatureCard 
            icon={Users}
            title="Real-time Updates"
            description="Parents receive instant notifications about attendance and progress"
          />
        </div>
      </Slide>

      {/* Slide 4: Market Opportunity */}
      <Slide id="slide-3">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold mb-8 text-gray-900 dark:text-white">Market Opportunity</h2>
        </div>
        
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-8">
            <StatCard 
              number="150M+" 
              label="Students in Africa"
              icon={Users}
            />
            <StatCard 
              number="$5B+" 
              label="EdTech TAM in Sub-Saharan Africa"
              icon={DollarSign}
            />
            <StatCard 
              number="70%" 
              label="Smartphone penetration growth"
              icon={TrendingUp}
            />
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
            <Globe className="w-12 h-12 text-[#1f7daf] mb-6" />
            <h3 className="text-2xl font-bold mb-4">Perfect Timing</h3>
            <ul className="space-y-3 text-gray-600 dark:text-gray-300">
              <li className="flex items-start gap-2">
                <div className="w-2 h-2 bg-[#1f7daf] rounded-full mt-2 flex-shrink-0"></div>
                <span>Rapid smartphone adoption across Africa</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-2 h-2 bg-[#1f7daf] rounded-full mt-2 flex-shrink-0"></div>
                <span>Mobile payments (M-Pesa) making digital solutions inevitable</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-2 h-2 bg-[#1f7daf] rounded-full mt-2 flex-shrink-0"></div>
                <span>Growing demand for educational transparency</span>
              </li>
            </ul>
          </div>
        </div>
      </Slide>

      {/* Slide 5: How It Works */}
      <Slide id="slide-4" className="bg-gradient-to-br from-purple-50/50 to-pink-50/50 dark:from-purple-900/10 dark:to-pink-900/10">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold mb-8 text-gray-900 dark:text-white">How It Works</h2>
        </div>
        
        <div className="grid md:grid-cols-4 gap-6">
          {[
            { step: "1", title: "Sign Up", desc: "Quick registration for schools and parents", color: "bg-blue-500" },
            { step: "2", title: "Chat Commands", desc: "Send messages like 'Register my school'", color: "bg-green-500" },
            { step: "3", title: "AI Guidance", desc: "System guides through setup and daily tasks", color: "bg-purple-500" },
            { step: "4", title: "Real-time Updates", desc: "Instant notifications and payments", color: "bg-orange-500" }
          ].map((item, index) => (
            <div key={index} className="text-center">
              <div className={`${item.color} w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-xl mx-auto mb-4`}>
                {item.step}
              </div>
              <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mt-12 max-w-2xl mx-auto">
          <div className="bg-gray-100 dark:bg-gray-800 rounded-xl p-6">
            <div className="text-sm text-gray-500 mb-2">Chat Example:</div>
            <div className="space-y-2">
              <div className="bg-[#1f7daf] text-white p-3 rounded-lg rounded-bl-sm max-w-xs">
                "Register my school - Sunrise Primary"
              </div>
              <div className="bg-white dark:bg-gray-700 p-3 rounded-lg rounded-br-sm max-w-xs ml-auto text-right">
                Great! I'll help you set up Sunrise Primary. How many students do you have?
              </div>
            </div>
          </div>
        </div>
      </Slide>

      {/* Slide 6: Traction */}
      <Slide id="slide-5">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold mb-8 text-gray-900 dark:text-white">Early Traction</h2>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
            <Award className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <div className="text-4xl font-bold text-green-500 mb-2">2</div>
            <div className="text-gray-600 dark:text-gray-300">Schools Onboarded</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
            <Users className="w-12 h-12 text-blue-500 mx-auto mb-4" />
            <div className="text-4xl font-bold text-blue-500 mb-2">390</div>
            <div className="text-gray-600 dark:text-gray-300">Students Managed</div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
            <TrendingUp className="w-12 h-12 text-purple-500 mx-auto mb-4" />
            <div className="text-4xl font-bold text-purple-500 mb-2">40%</div>
            <div className="text-gray-600 dark:text-gray-300">Admin Time Reduced</div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mt-12 max-w-3xl mx-auto">
          <h3 className="text-2xl font-bold mb-6 text-center">Early Feedback</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-green-50 dark:bg-green-900/20 p-6 rounded-xl">
              <div className="text-4xl mb-3">✨</div>
              <p className="text-gray-700 dark:text-gray-300 italic">
                "The chat interface is so intuitive. Our teachers love how easy it is to update attendance."
              </p>
              <p className="text-sm text-gray-500 mt-3">- School Principal</p>
            </div>
            <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-xl">
              <div className="text-4xl mb-3">📱</div>
              <p className="text-gray-700 dark:text-gray-300 italic">
                "Finally, I get real-time updates about my child's school activities on my phone."
              </p>
              <p className="text-sm text-gray-500 mt-3">- Parent</p>
            </div>
          </div>
        </div>
      </Slide>

      {/* Slide 7: Business Model */}
      <Slide id="slide-6" className="bg-gradient-to-br from-green-50/50 to-teal-50/50 dark:from-green-900/10 dark:to-teal-900/10">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold mb-8 text-gray-900 dark:text-white">Business Model</h2>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
            <DollarSign className="w-12 h-12 text-green-500 mb-6" />
            <h3 className="text-xl font-bold mb-4">SaaS Subscriptions</h3>
            <p className="text-gray-600 dark:text-gray-300 mb-4">Tiered pricing based on school size</p>
            <ul className="space-y-2 text-sm">
              <li>• Small (≤100 students): $50/month</li>
              <li>• Medium (101-500): $150/month</li>
              <li>• Large (500+): $300/month</li>
            </ul>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
            <TrendingUp className="w-12 h-12 text-blue-500 mb-6" />
            <h3 className="text-xl font-bold mb-4">Transaction Fees</h3>
            <p className="text-gray-600 dark:text-gray-300 mb-4">Revenue from payment processing</p>
            <ul className="space-y-2 text-sm">
              <li>• 2-3% on school fee payments</li>
              <li>• M-Pesa integration fees</li>
              <li>• Card processing revenue</li>
            </ul>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
            <Rocket className="w-12 h-12 text-purple-500 mb-6" />
            <h3 className="text-xl font-bold mb-4">Future Revenue</h3>
            <p className="text-gray-600 dark:text-gray-300 mb-4">Value-added services</p>
            <ul className="space-y-2 text-sm">
              <li>• Educational loans</li>
              <li>• Insurance products</li>
              <li>• Learning content licensing</li>
            </ul>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mt-12 max-w-2xl mx-auto text-center">
          <h3 className="text-2xl font-bold mb-4">Revenue Projection</h3>
          <div className="text-3xl font-bold text-[#1f7daf] mb-2">$2.5M ARR</div>
          <p className="text-gray-600 dark:text-gray-300">By Year 3 with 500 schools</p>
        </div>
      </Slide>

      {/* Slide 8: Competition */}
      <Slide id="slide-7">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold mb-8 text-gray-900 dark:text-white">Competitive Advantage</h2>
        </div>
        
        <div className="grid md:grid-cols-2 gap-12">
          <div className="space-y-6">
            <h3 className="text-2xl font-bold text-red-600">Traditional Systems</h3>
            <div className="space-y-4">
              {[
                "Bulky, expensive desktop software",
                "High learning curve for staff",
                "Poor mobile experience",
                "Limited payment integration",
                "Expensive implementation"
              ].map((item, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span className="text-gray-600 dark:text-gray-300">{item}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="space-y-6">
            <h3 className="text-2xl font-bold text-[#1f7daf]">Olaji Differentiators</h3>
            <div className="space-y-4">
              {[
                "Chat-first interface (zero learning curve)",
                "Mobile-native design",
                "Embedded payment processing",
                "Affordable, flexible pricing",
                "AI-powered assistance"
              ].map((item, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-[#1f7daf] rounded-full"></div>
                  <span className="text-gray-600 dark:text-gray-300">{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mt-12 max-w-3xl mx-auto text-center">
          <Target className="w-16 h-16 text-[#1f7daf] mx-auto mb-6" />
          <h3 className="text-2xl font-bold mb-4">Our Moat</h3>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            First-mover advantage in chat-based school management for Africa, 
            with deep mobile payments integration and AI assistance
          </p>
        </div>
      </Slide>

      {/* Slide 9: Vision */}
      <Slide id="slide-8" className="bg-gradient-to-br from-indigo-50/50 to-purple-50/50 dark:from-indigo-900/10 dark:to-purple-900/10">
        <div className="text-center">
          <h2 className="text-5xl font-bold mb-12 text-gray-900 dark:text-white">Our Vision</h2>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-12 max-w-4xl mx-auto">
            <div className="text-6xl mb-8">🌍</div>
            <h3 className="text-4xl font-bold mb-8 bg-gradient-to-r from-[#1f7daf] to-[#104f73] bg-clip-text text-transparent">
              Financial OS for Education in Africa
            </h3>
            
            <div className="grid md:grid-cols-3 gap-8 mt-12">
              <div>
                <div className="text-2xl mb-4">📚</div>
                <h4 className="font-bold mb-2">Digital Identity</h4>
                <p className="text-gray-600 dark:text-gray-300 text-sm">
                  Every student's academic journey stored securely
                </p>
              </div>
              
              <div>
                <div className="text-2xl mb-4">💳</div>
                <h4 className="font-bold mb-2">Financial Rails</h4>
                <p className="text-gray-600 dark:text-gray-300 text-sm">
                  Seamless payments and financial services for families
                </p>
              </div>
              
              <div>
                <div className="text-2xl mb-4">🤝</div>
                <h4 className="font-bold mb-2">Ecosystem Platform</h4>
                <p className="text-gray-600 dark:text-gray-300 text-sm">
                  Connect schools, parents, and educational services
                </p>
              </div>
            </div>
          </div>
        </div>
      </Slide>

      {/* Slide 10: Team */}
      <Slide id="slide-9">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold mb-8 text-gray-900 dark:text-white">The Team</h2>
        </div>
        
        <div className="grid md:grid-cols-2 gap-12 max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
            <div className="w-24 h-24 bg-gradient-to-br from-[#1f7daf] to-[#104f73] rounded-full mx-auto mb-6 flex items-center justify-center text-white text-2xl font-bold">
              EM
            </div>
            <h3 className="text-2xl font-bold mb-2">Eric Munene Mwirichia</h3>
            <p className="text-[#1f7daf] font-medium mb-4">Co-founder & CEO</p>
            <ul className="text-left space-y-2 text-gray-600 dark:text-gray-300">
              <li>• Tech lead with startup experience</li>
              <li>• Former Circularity Space team member</li>
              <li>• Multiple successful ventures</li>
              <li>• Deep understanding of African markets</li>
            </ul>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center border-2 border-dashed border-gray-300">
            <div className="w-24 h-24 bg-gray-200 dark:bg-gray-700 rounded-full mx-auto mb-6 flex items-center justify-center text-4xl">
              ?
            </div>
            <h3 className="text-2xl font-bold mb-2">Co-founder/COO</h3>
            <p className="text-gray-500 font-medium mb-4">Position Open</p>
            <ul className="text-left space-y-2 text-gray-600 dark:text-gray-300">
              <li>• School partnerships & operations</li>
              <li>• Business development</li>
              <li>• Customer success</li>
              <li>• African education sector experience</li>
            </ul>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mt-12 max-w-2xl mx-auto text-center">
          <h3 className="text-xl font-bold mb-4">Advisory Board</h3>
          <p className="text-gray-600 dark:text-gray-300">
            Building relationships with EdTech veterans, fintech experts, 
            and African education leaders to guide our growth
          </p>
        </div>
      </Slide>

      {/* Slide 11: The Ask */}
      <Slide id="slide-10" className="bg-gradient-to-br from-orange-50/50 to-red-50/50 dark:from-orange-900/10 dark:to-red-900/10">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold mb-8 text-gray-900 dark:text-white">The Ask</h2>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-12 max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <div className="text-6xl font-bold text-[#1f7daf] mb-4">$500K</div>
            <p className="text-xl text-gray-600 dark:text-gray-300">Seed funding for 18 months runway</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Rocket className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="font-bold mb-2">Product Development</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">AI assistant enhancement & payment integrations</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="font-bold mb-2">School Onboarding</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">Sales team & partnership development</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Globe className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="font-bold mb-2">Market Expansion</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">Kenya growth, Uganda & Ghana entry</p>
            </div>
          </div>
          
          <div className="mt-12 p-6 bg-gray-50 dark:bg-gray-800 rounded-xl">
            <h3 className="text-xl font-bold mb-4 text-center">18-Month Milestones</h3>
            <div className="grid md:grid-cols-3 gap-6 text-center">
              <div>
                <div className="text-2xl font-bold text-[#1f7daf]">50+</div>
                <div className="text-sm text-gray-600 dark:text-gray-300">Schools Onboarded</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-[#1f7daf]">10K+</div>
                <div className="text-sm text-gray-600 dark:text-gray-300">Students Managed</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-[#1f7daf]">3</div>
                <div className="text-sm text-gray-600 dark:text-gray-300">Countries Active</div>
              </div>
            </div>
          </div>
        </div>
      </Slide>

      {/* Slide 12: Closing */}
      <Slide id="slide-11" className="bg-gradient-to-br from-[#1f7daf]/5 to-[#104f73]/5">
        <div className="text-center">
          <Logo size="lg" className="justify-center mb-8" />
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-[#1f7daf] to-[#104f73] bg-clip-text text-transparent">
            Simplifying school management,
            <br />
            one chat at a time
          </h1>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 max-w-2xl mx-auto mt-12">
            <h3 className="text-2xl font-bold mb-6">Let's Connect</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-3">
                <div className="w-2 h-2 bg-[#1f7daf] rounded-full"></div>
                <span className="text-lg">eric@olaji.io</span>
              </div>
              <div className="flex items-center justify-center gap-3">
                <div className="w-2 h-2 bg-[#1f7daf] rounded-full"></div>
                <span className="text-lg">+254 xxx xxx xxx</span>
              </div>
              <div className="flex items-center justify-center gap-3">
                <div className="w-2 h-2 bg-[#1f7daf] rounded-full"></div>
                <span className="text-lg">linkedin.com/in/ericmunene</span>
              </div>
            </div>
            
            <div className="mt-8 p-4 bg-[#1f7daf]/10 rounded-xl">
              <p className="text-[#1f7daf] font-medium">
                Ready to transform education in Africa? 
                <br />
                Let's build the future together.
              </p>
            </div>
          </div>
          
          <div className="mt-12 text-center">
            <p className="text-gray-500 text-sm">
              Pitch Deck v1.0 • Confidential • © 2025 Olaji
            </p>
          </div>
        </div>
      </Slide>
    </div>
  );
}