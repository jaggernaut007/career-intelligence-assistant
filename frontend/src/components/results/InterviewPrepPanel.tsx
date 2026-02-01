import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { InterviewQuestion } from '../../types/specs';
import { ChevronDown, ChevronUp, MessageCircle, Star } from 'lucide-react';

interface InterviewPrepPanelProps {
  questions: InterviewQuestion[];
}

export const InterviewPrepPanel: React.FC<InterviewPrepPanelProps> = ({ questions }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  if (questions.length === 0) {
    return (
        <Card className="p-6 text-center text-gray-500">
            <MessageCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No interview questions generated yet.</p>
        </Card>
    );
  }

  return (
    <div className="space-y-4">
      {questions.map((q) => (
        <Card 
            key={q.id} 
            className={`transition-all duration-200 cursor-pointer border ${expandedId === q.id ? 'border-primary-200 ring-2 ring-primary-50' : 'hover:border-primary-100'}`}
            onClick={() => toggleExpand(q.id)}
        >
          <div className="p-4">
            <div className="flex justify-between items-start mb-2">
               <div className="flex-1 pr-4">
                   <h4 className="font-semibold text-gray-900 text-lg flex items-start gap-2">
                       <span className="text-primary-600 mt-1"><MessageCircle className="w-5 h-5"/></span>
                       {q.question}
                   </h4>
               </div>
               <div className="flex flex-col items-end gap-2">
                    <Badge variant={q.difficulty === 'hard' ? 'danger' : q.difficulty === 'medium' ? 'warning' : 'success'}>
                        {q.difficulty.toUpperCase()}
                    </Badge>
                   {expandedId === q.id ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
               </div>
            </div>

            {expandedId === q.id && (
              <div className="mt-4 pt-4 border-t border-gray-100 space-y-4 animate-fadeIn">
                <div className="bg-gray-50 p-3 rounded-md">
                    <p className="text-sm text-gray-600 font-medium mb-1">Why they ask this:</p>
                    <p className="text-sm text-gray-700 italic">{q.whyAsked}</p>
                </div>

                <div>
                    <h5 className="text-sm font-bold text-gray-900 mb-2">Suggested Answer</h5>
                    <p className="text-gray-700 text-sm leading-relaxed">{q.suggestedAnswer}</p>
                </div>

                {q.starExample && (
                    <div className="border border-blue-100 bg-blue-50 p-4 rounded-md">
                        <h5 className="text-sm font-bold text-blue-900 mb-3 flex items-center">
                            <Star className="w-4 h-4 mr-1 text-blue-500" fill="currentColor" />
                            STAR Method Example
                        </h5>
                        <div className="grid grid-cols-1 gap-3 text-sm">
                            <div><span className="font-bold text-blue-800">Situation:</span> {q.starExample.situation}</div>
                            <div><span className="font-bold text-blue-800">Task:</span> {q.starExample.task}</div>
                            <div><span className="font-bold text-blue-800">Action:</span> {q.starExample.action}</div>
                            <div><span className="font-bold text-blue-800">Result:</span> {q.starExample.result}</div>
                        </div>
                    </div>
                )}
              </div>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
};
