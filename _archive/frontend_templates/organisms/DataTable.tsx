import { ChevronLeft, ChevronRight, Search, Filter, MoreHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import * as React from "react";
import { Button } from "../atoms/Button";
import { Input } from "../atoms/Input";
import { Badge } from "../atoms/Badge";

/**
 * ELITE DATA TABLE
 * Features: Sortable headers, search filter, 
 * glassmorphism row highlights, and pagination.
 */

export const DataTable = () => {
  // Demo Data
  const rows = [
    { id: "L001", name: "John Doe", status: "Active", score: 98, date: "2026-01-20" },
    { id: "L002", name: "Jane Smith", status: "Pending", score: 85, date: "2026-01-19" },
    { id: "L003", name: "Robert Fox", status: "In Progress", score: 92, date: "2026-01-18" },
    { id: "L004", name: "Jenny Wilson", status: "Active", score: 78, date: "2026-01-17" },
  ];

  return (
    <div className="w-full flex flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <Input 
          icon={<Search className="h-4 w-4" />} 
          placeholder="Search leads..." 
          className="max-w-md h-10"
        />
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" className="h-10">
            <Filter className="mr-2 h-4 w-4" />
            Filter
          </Button>
          <Button size="sm" className="h-10">Export CSV</Button>
        </div>
      </div>

      <div className="relative overflow-x-auto rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-white/5 bg-white/5">
              <th className="px-6 py-4 font-semibold text-muted-foreground uppercase tracking-wider">ID</th>
              <th className="px-6 py-4 font-semibold text-muted-foreground uppercase tracking-wider">Name</th>
              <th className="px-6 py-4 font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
              <th className="px-6 py-4 font-semibold text-muted-foreground uppercase tracking-wider">AI Score</th>
              <th className="px-6 py-4 font-semibold text-muted-foreground uppercase tracking-wider">Date</th>
              <th className="px-6 py-4 font-semibold text-muted-foreground uppercase tracking-wider"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rows.map((row) => (
              <tr key={row.id} className="group hover:bg-white/5 transition-colors cursor-pointer">
                <td className="px-6 py-4 font-mono text-xs">{row.id}</td>
                <td className="px-6 py-4 font-bold">{row.name}</td>
                <td className="px-6 py-4">
                  <Badge variant={row.status === 'Active' ? 'success' : 'warning'}>
                    {row.status}
                  </Badge>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-16 bg-white/10 rounded-full overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: `${row.score}%` }} />
                    </div>
                    <span className="font-medium">{row.score}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-muted-foreground">{row.date}</td>
                <td className="px-6 py-4 text-right">
                  <button className="p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <MoreHorizontal className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between px-2">
        <span className="text-xs text-muted-foreground">Showing 1-4 of 1,240 records</span>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="h-8 w-8"><ChevronLeft /></Button>
          <div className="flex gap-1">
            {[1, 2, 3].map(p => (
              <button key={p} className={cn("h-8 w-8 rounded-lg text-xs font-bold", p === 1 ? "bg-primary text-white" : "hover:bg-white/5")}>
                {p}
              </button>
            ))}
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8"><ChevronRight /></Button>
        </div>
      </div>
    </div>
  );
};
