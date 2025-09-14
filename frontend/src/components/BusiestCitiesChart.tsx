import { TrendingUp } from "lucide-react";
import { Bar, BarChart, XAxis, YAxis } from "recharts";

// Type definition matching your existing BusiestCity type
interface BusiestCity {
  city: string;
  total_attendance: number;
  top_events: any[];
}

interface BusiestCitiesChartProps {
  busiestCities: BusiestCity[];
}

export function BusiestCitiesChart({ busiestCities }: BusiestCitiesChartProps) {
  // Transform the busiest cities data for the chart
  const chartData = busiestCities.map((city, index) => ({
    city: city.city,
    attendance: city.total_attendance,
    fill: `hsl(${index * 45}, 70%, 50%)`, // Generate different colors
  }));

  if (!busiestCities || busiestCities.length === 0) {
    return null;
  }

  const totalAttendance = busiestCities.reduce((sum, city) => sum + city.total_attendance, 0);
  const topCity = busiestCities[0];

  return (
    <div style={{
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderRadius: '8px',
      padding: '16px',
      margin: '16px 0',
      color: 'white',
      border: '1px solid rgba(255, 255, 255, 0.1)'
    }}>
      {/* Header */}
      <div style={{ marginBottom: '16px' }}>
        <h3 style={{ margin: '0 0 4px 0', fontSize: '18px', fontWeight: '600' }}>
          Event Attendance by City
        </h3>
        <p style={{ margin: 0, fontSize: '14px', color: 'rgba(255, 255, 255, 0.7)' }}>
          Top {busiestCities.length} cities by total event attendance
        </p>
      </div>

      {/* Chart */}
      <div style={{ width: '100%', height: '200px' }}>
        <BarChart
          width={400}
          height={200}
          data={chartData}
          layout="vertical"
          margin={{ left: 80, right: 20, top: 5, bottom: 5 }}
        >
          <XAxis 
            type="number" 
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'white', fontSize: 12 }}
          />
          <YAxis 
            type="category" 
            dataKey="city"
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'white', fontSize: 12 }}
            width={75}
          />
          <Bar 
            dataKey="attendance" 
            radius={[0, 4, 4, 0]}
            />
        </BarChart>
      </div>

      {/* Footer */}
      <div style={{ marginTop: '16px', fontSize: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '500', marginBottom: '4px' }}>
          {topCity && (
            <>
              {topCity.city} leads with {topCity.total_attendance.toLocaleString()} total attendance
              <TrendingUp size={16} />
            </>
          )}
        </div>
        <div style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
          Combined attendance across all cities: {totalAttendance.toLocaleString()}
        </div>
      </div>
    </div>
  );
}