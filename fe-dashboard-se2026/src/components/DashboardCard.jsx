export default function DashboardCard({ title, value, color }) {
  return (
    <div className={`p-6 rounded-2xl shadow-lg bg-white border-l-8 ${color}`}>
      <h3 className="text-gray-500 text-sm font-semibold uppercase">{title}</h3>
      <p className="text-4xl font-bold mt-2 text-gray-800">{value}</p>
    </div>
  );
}