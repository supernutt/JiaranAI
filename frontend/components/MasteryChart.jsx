'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Line, ComposedChart } from 'recharts';

const MasteryChart = ({ history }) => {
  // No data case
  if (!history || history.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 mt-6 w-full max-w-md mx-auto h-[300px] flex items-center justify-center text-muted-foreground dark:bg-gray-800 dark:text-gray-400">
        Answer questions to see your mastery progress
      </div>
    );
  }

  // Format concept name for display
  const formatConceptName = (concept) => {
    return concept
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Group history by concept
  const groupedHistoryByConcept = {};
  history.forEach((entry) => {
    const { concept, belief } = entry;
    if (!concept || !belief) {
      console.warn("Skipping history entry due to missing concept or belief:", entry);
      return;
    }
    if (!groupedHistoryByConcept[concept]) {
      groupedHistoryByConcept[concept] = [];
    }
    groupedHistoryByConcept[concept].push({ belief });
  });

  // Create distribution data for each concept - take only the most recent belief
  const currentDistributionPerConcept = {};
  Object.entries(groupedHistoryByConcept).forEach(([concept, snapshots]) => {
    if (snapshots.length === 0) return;
    
    // Get the most recent belief distribution
    const mostRecentBelief = snapshots[snapshots.length - 1].belief;
    
    // Transform to x-axis = ability level, y-axis = probability
    const distributionData = [];
    if (Array.isArray(mostRecentBelief)) {
      mostRecentBelief.forEach(point => {
        if (typeof point.a === 'number' && typeof point.p === 'number') {
          distributionData.push({
            ability: point.a.toFixed(1),
            probability: point.p
          });
        }
      });
    }
    
    currentDistributionPerConcept[concept] = distributionData;
  });

  return (
    <div className="bg-card border border-border rounded-lg p-5 mt-2 md:mt-6 w-full dark:bg-gray-800 sticky top-24">
      <h3 className="text-lg font-medium mb-4 text-center text-gray-900 dark:text-white">Current Belief Distribution</h3>
      
      {Object.keys(currentDistributionPerConcept).length === 0 && (
        <div className="text-center text-muted-foreground dark:text-gray-400 py-10">
          No belief data processed. Ensure 'history' prop contains valid 'concept' and 'belief' arrays.
        </div>
      )}

      <div className="flex flex-col gap-5">
        {Object.entries(currentDistributionPerConcept).map(([concept, data]) => {
          if (data.length === 0) return null;
          return (
            <div key={concept} className="rounded-xl p-4 shadow-md border bg-white dark:bg-gray-900">
              <h4 className="text-lg font-medium mb-3 text-center text-gray-800 dark:text-gray-100">{formatConceptName(concept)}</h4>
              <div className="flex justify-center">
                <div className="w-full" style={{ height: 220 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                      data={data}
                      margin={{ top: 5, right: 25, left: 0, bottom: 20 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis 
                        dataKey="ability" 
                        label={{ value: 'Ability Level', position: 'insideBottom', offset: -10, fontSize: 12, fill: '#666' }}
                        tick={{ fontSize: 10, fill: '#666' }}
                      />
                      <YAxis 
                        domain={[0, 0.3]} 
                        ticks={[0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]} 
                        label={{ value: 'Probability', angle: -90, position: 'insideLeft', offset: 10, fontSize: 12, fill: '#666' }}
                        tickFormatter={(tick) => tick.toFixed(2)}
                        tick={{ fontSize: 10, fill: '#666' }}
                      />
                      <Tooltip 
                        formatter={(value) => [parseFloat(value).toFixed(3), 'Probability']}
                        labelFormatter={(label) => `Ability ${label}`}
                        contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: '4px', border: '1px solid #ccc' }}
                      />
                      <Legend wrapperStyle={{ fontSize: 10, marginTop: '5px' }} />
                      <Area 
                        type="monotone"
                        dataKey="probability" 
                        name="Probability" 
                        fill="#8884d8"
                        fillOpacity={0.4}
                        stroke="none"
                      />
                      <Line 
                        type="monotone"
                        dataKey="probability" 
                        name="Probability" 
                        stroke="#6366f1"
                        strokeWidth={2}
                        dot={{ r: 3, fill: '#6366f1' }}
                        activeDot={{ r: 5 }}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="mt-8 text-center">
        <p className="text-sm text-muted-foreground">
          The chart shows your current belief distribution for each concept.
          Higher probabilities at higher ability levels indicate stronger mastery.
        </p>
      </div>
    </div>
  );
};

export default MasteryChart; 