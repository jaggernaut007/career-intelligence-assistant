import React from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Recommendation } from '../../types/specs';
import { Lightbulb, Clock, CheckCircle2, ArrowRight } from 'lucide-react';

interface RecommendationListProps {
  recommendations: Recommendation[];
}

export const RecommendationList: React.FC<RecommendationListProps> = ({ recommendations }) => {
  // Sort by priority: high -> medium -> low
  const sortedRecommendations = [...recommendations].sort((a, b) => {
    const priorities = { high: 3, medium: 2, low: 1 };
    return priorities[b.priority] - priorities[a.priority];
  });

  if (recommendations.length === 0) {
      return (
          <Card className="p-6">
              <div className="text-center text-gray-500 py-8">
                  <Lightbulb className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No recommendations available yet. Complete the analysis to get personalized advice.</p>
              </div>
          </Card>
      );
  }

  return (
    <div className="space-y-4">
      {sortedRecommendations.map((rec) => (
        <Card key={rec.id} className="p-0 overflow-hidden border-l-4 border-l-primary-500">
          <div className="p-5">
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center gap-2">
                 <h4 className="font-semibold text-gray-900 text-lg">{rec.title}</h4>
                 <Badge variant={rec.priority === 'high' ? 'danger' : rec.priority === 'medium' ? 'warning' : 'default'}>
                     {rec.priority.toUpperCase()}
                 </Badge>
              </div>
              <Badge variant="outline" className="text-xs bg-gray-50 uppercase tracking-wider">
                {rec.category.replace('_', ' ')}
              </Badge>
            </div>
            
            <p className="text-gray-600 mb-4">{rec.description}</p>
            
            <div className="space-y-2 mb-4">
                <h5 className="text-sm font-medium text-gray-900 flex items-center">
                    <CheckCircle2 className="w-4 h-4 mr-2 text-green-600" />
                    Action Items:
                </h5>
                <ul className="list-disc list-inside text-sm text-gray-700 pl-2 space-y-1">
                    {rec.actionItems.map((item, idx) => (
                        <li key={idx} className="pl-4 -indent-4">{item}</li>
                    ))}
                </ul>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                {rec.estimatedTime && (
                    <div className="flex items-center text-xs text-gray-500">
                        <Clock className="w-3 h-3 mr-1" />
                        Est. Time: {rec.estimatedTime}
                    </div>
                )}
                
                {rec.resources.length > 0 && (
                     <a href={rec.resources[0]} target="_blank" rel="noopener noreferrer" className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center hover:underline">
                        View Resources <ArrowRight className="w-3 h-3 ml-1" />
                     </a>
                )}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};
