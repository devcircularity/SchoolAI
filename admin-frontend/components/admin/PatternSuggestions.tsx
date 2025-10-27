// components/admin/PatternSuggestions.tsx
import React, { useState } from 'react';
import { Lightbulb, Copy, CheckCircle } from 'lucide-react';
import Button from '@/components/ui/Button';

interface PatternSuggestion {
  name: string;
  description: string;
  pattern: string;
  example_matches: string[];
  category: 'student' | 'payment' | 'class' | 'general' | 'invoice' | 'overview';
}

interface PatternSuggestionsProps {
  intent: string;
  handler: string;
  onSelectPattern: (pattern: string) => void;
}

export function PatternSuggestions({ intent, handler, onSelectPattern }: PatternSuggestionsProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [copiedPattern, setCopiedPattern] = useState<string>('');

  const patternSuggestions: PatternSuggestion[] = [
    // Student Management
    {
      name: 'Create Student',
      description: 'Matches requests to create or add new students',
      pattern: '(create|add|register|new)\\s+(student|pupil|learner)',
      example_matches: ['create student', 'add new student', 'register pupil'],
      category: 'student'
    },
    {
      name: 'List Students',
      description: 'Matches requests to view or list students',
      pattern: '(list|show|display|view)\\s+(students?|pupils?|learners?)',
      example_matches: ['list students', 'show all students', 'display pupils'],
      category: 'student'
    },
    {
      name: 'Student Count',
      description: 'Matches questions about number of students',
      pattern: '(how\\s+many|number\\s+of|count).*students?',
      example_matches: ['how many students', 'number of students', 'student count'],
      category: 'student'
    },
    {
      name: 'Search Students',
      description: 'Matches student search requests',
      pattern: '(search|find|look\\s+for)\\s+(student|pupil)',
      example_matches: ['search student', 'find pupil', 'look for student'],
      category: 'student'
    },

    // Payment Management
    {
      name: 'Record Payment',
      description: 'Matches requests to record or process payments',
      pattern: '(record|make|process|add)\\s+payment',
      example_matches: ['record payment', 'make payment', 'process payment'],
      category: 'payment'
    },
    {
      name: 'Payment History',
      description: 'Matches requests for payment history or records',
      pattern: '(payment|fee)\\s+(history|records?|transactions?)',
      example_matches: ['payment history', 'fee records', 'payment transactions'],
      category: 'payment'
    },
    {
      name: 'Payment Status',
      description: 'Matches payment status inquiries',
      pattern: '(payment|fee)\\s+(status|check)',
      example_matches: ['payment status', 'check payment', 'fee status'],
      category: 'payment'
    },

    // Class Management
    {
      name: 'Create Class',
      description: 'Matches requests to create new classes',
      pattern: '(create|add|make|new)\\s+(class|grade)',
      example_matches: ['create class', 'add new class', 'make grade'],
      category: 'class'
    },
    {
      name: 'List Classes',
      description: 'Matches requests to view classes',
      pattern: '(list|show|display)\\s+(classes?|grades?)',
      example_matches: ['list classes', 'show grades', 'display all classes'],
      category: 'class'
    },

    // Invoice Management
    {
      name: 'Generate Invoice',
      description: 'Matches invoice generation requests',
      pattern: '(generate|create|make)\\s+(invoice|bill)',
      example_matches: ['generate invoice', 'create bill', 'make invoice'],
      category: 'invoice'
    },
    {
      name: 'Invoice List',
      description: 'Matches requests to view invoices',
      pattern: '(list|show|view)\\s+(invoices?|bills?)',
      example_matches: ['list invoices', 'show bills', 'view all invoices'],
      category: 'invoice'
    },

    // General/Overview
    {
      name: 'School Overview',
      description: 'Matches requests for school summary or dashboard',
      pattern: '(school|overview|summary|dashboard)',
      example_matches: ['school overview', 'dashboard', 'summary'],
      category: 'overview'
    },
    {
      name: 'Help Request',
      description: 'Matches general help requests',
      pattern: '(help|assistance|support|what\\s+can)',
      example_matches: ['help', 'need assistance', 'what can you do'],
      category: 'general'
    },
    {
      name: 'Greeting',
      description: 'Matches common greetings',
      pattern: '(hello|hi|hey|good\\s+(morning|afternoon|evening))',
      example_matches: ['hello', 'hi there', 'good morning'],
      category: 'general'
    }
  ];

  // Filter suggestions based on intent, handler, and category
  const getRelevantSuggestions = () => {
    let filtered = patternSuggestions;

    // Filter by category if selected
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(s => s.category === selectedCategory);
    }

    // Smart filtering based on intent/handler
    if (intent || handler) {
      const searchTerms = `${intent} ${handler}`.toLowerCase();
      filtered = filtered.filter(s => {
        const suggestionTerms = `${s.name} ${s.description} ${s.category}`.toLowerCase();
        return searchTerms.split(' ').some(term => 
          term.length > 2 && suggestionTerms.includes(term)
        );
      });
    }

    return filtered;
  };

  const handleCopyPattern = (pattern: string) => {
    onSelectPattern(pattern);
    setCopiedPattern(pattern);
    setTimeout(() => setCopiedPattern(''), 2000);
  };

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'student', label: 'Student Management' },
    { value: 'payment', label: 'Payments & Fees' },
    { value: 'class', label: 'Class Management' },
    { value: 'invoice', label: 'Invoices' },
    { value: 'overview', label: 'Overview & Dashboard' },
    { value: 'general', label: 'General' }
  ];

  const relevantSuggestions = getRelevantSuggestions();

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-blue-600">
        <Lightbulb size={16} />
        <h4 className="font-medium">Pattern Suggestions</h4>
      </div>

      {/* Category Filter */}
      <div>
        <label className="block text-sm font-medium mb-2">Category</label>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="input w-full"
        >
          {categories.map(cat => (
            <option key={cat.value} value={cat.value}>{cat.label}</option>
          ))}
        </select>
      </div>

      {/* Suggestions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto">
        {relevantSuggestions.length === 0 ? (
          <div className="col-span-2 text-center py-8 text-gray-500">
            <p>No suggestions found for the current intent/handler.</p>
            <p className="text-sm mt-1">Try selecting "All Categories" or a different category.</p>
          </div>
        ) : (
          relevantSuggestions.map((suggestion, index) => (
            <div
              key={index}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:border-blue-300 dark:hover:border-blue-600 transition-colors"
            >
              <div className="flex justify-between items-start mb-2">
                <h5 className="font-medium text-sm">{suggestion.name}</h5>
                <span className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                  {suggestion.category}
                </span>
              </div>
              
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
                {suggestion.description}
              </p>
              
              <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded mb-3">
                <code className="text-xs font-mono">{suggestion.pattern}</code>
              </div>
              
              <div className="mb-3">
                <p className="text-xs font-medium mb-1">Example matches:</p>
                <div className="flex flex-wrap gap-1">
                  {suggestion.example_matches.map((example, i) => (
                    <span
                      key={i}
                      className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-2 py-1 rounded"
                    >
                      "{example}"
                    </span>
                  ))}
                </div>
              </div>
              
              <Button
                onClick={() => handleCopyPattern(suggestion.pattern)}
                className="btn-sm btn-secondary w-full flex items-center justify-center gap-2"
              >
                {copiedPattern === suggestion.pattern ? (
                  <>
                    <CheckCircle size={14} />
                    Applied!
                  </>
                ) : (
                  <>
                    <Copy size={14} />
                    Use This Pattern
                  </>
                )}
              </Button>
            </div>
          ))
        )}
      </div>

      {/* Quick Tips */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
        <h5 className="font-medium text-sm mb-2">Pattern Writing Tips</h5>
        <ul className="text-xs space-y-1 text-gray-700 dark:text-gray-300">
          <li>• Use <code>(option1|option2)</code> for alternatives: <code>(create|add|make)</code></li>
          <li>• Use <code>.*</code> to match any characters: <code>student.*details</code></li>
          <li>• Use <code>\\s+</code> for one or more spaces: <code>create\\s+student</code></li>
          <li>• Use <code>?</code> to make parts optional: <code>students?</code> matches both "student" and "students"</li>
          <li>• Use <code>^</code> to match start of message: <code>^hello</code></li>
          <li>• Use <code>$</code> to match end of message: <code>please$</code></li>
        </ul>
      </div>
    </div>
  );
}