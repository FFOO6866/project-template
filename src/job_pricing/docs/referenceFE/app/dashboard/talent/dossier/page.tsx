"use client"

import { useState } from "react"
import Image from "next/image"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"

/* -------------------------------------------------------------------------- */
/*                                   Types                                    */
/* -------------------------------------------------------------------------- */

interface Employee {
  id: string
  name: string
  role: string
  department: string
  joined: string
  reportsTo: string
  teamSize: string
  image: string
}

interface CareerMilestone {
  date: string
  title: string
  description: string
}

/* -------------------------------------------------------------------------- */
/*                               Static Content                               */
/* -------------------------------------------------------------------------- */

const employees: Employee[] = [
  {
    id: "lim-wei-ming",
    name: "Lim Wei Ming",
    role: "Chief People Officer",
    department: "People & Organisation",
    joined: "March 2016",
    reportsTo: "CEO, TPC Group",
    teamSize: "25 direct reports",
    image: "/confident-professional.png",
  },
  {
    id: "sarah-tan-hui-ling",
    name: "Sarah Tan Hui Ling",
    role: "Director, Talent Management",
    department: "People & Organisation",
    joined: "June 2018",
    reportsTo: "Lim Wei Ming, CPO",
    teamSize: "12 direct reports",
    image: "/team/sarah-chen.jpg",
  },
  {
    id: "marcus-wong-kai-jun",
    name: "Marcus Wong Kai Jun",
    role: "Assistant Director, Total Rewards",
    department: "People & Organisation",
    joined: "January 2019",
    reportsTo: "Sarah Tan, Director",
    teamSize: "8 direct reports",
    image: "/team/james-wilson.jpg",
  },
  {
    id: "jennifer-loh-mei-hua",
    name: "Jennifer Loh Mei Hua",
    role: "Senior Manager, Property Development",
    department: "TPC Properties",
    joined: "August 2017",
    reportsTo: "David Chua, VP Properties",
    teamSize: "15 direct reports",
    image: "/team/olivia-martinez.jpg",
  },
  {
    id: "david-chen-wei-liang",
    name: "David Chen Wei Liang",
    role: "Hotel Operations Manager",
    department: "TPC Hospitality",
    joined: "April 2020",
    reportsTo: "Rachel Ng, Hotel Director",
    teamSize: "45 direct reports",
    image: "/team/robert-chen.jpg",
  },
  {
    id: "rachel-ng-siew-hong",
    name: "Rachel Ng Siew Hong",
    role: "Hotel Director",
    department: "TPC Hospitality",
    joined: "February 2015",
    reportsTo: "CEO, TPC Hospitality",
    teamSize: "120 direct reports",
    image: "/team/michael-rodriguez.jpg",
  },
]

const careerMilestones: Record<string, CareerMilestone[]> = {
  "lim-wei-ming": [
    {
      date: "March 2016",
      title: "Joined as HR Director",
      description: "Began leading the transformation of people practices across the conglomerate.",
    },
    {
      date: "November 2017",
      title: "Digital HR Transformation",
      description: "Implemented a group-wide HRIS, improving HR efficiency by 40 %.",
    },
    {
      date: "June 2018",
      title: "Promoted to Chief People Officer",
      description: "Assumed oversight of talent management and organisational development.",
    },
    {
      date: "January 2019",
      title: "TPC Leadership Academy Launch",
      description: "Founded an internal leadership programme training 200+ managers annually.",
    },
  ],
  "sarah-tan-hui-ling": [
    {
      date: "June 2018",
      title: "Joined TPC Group",
      description: "Brought in to build the talent management centre of excellence.",
    },
    {
      date: "May 2020",
      title: "Succession Planning Framework",
      description: "Rolled out succession plans covering 95 % of leadership roles.",
    },
  ],
  "marcus-wong-kai-jun": [
    {
      date: "January 2019",
      title: "Joined Total Rewards Team",
      description: "Introduced a pay-for-performance salary architecture.",
    },
    {
      date: "September 2021",
      title: "Regional Job Evaluation Roll-out",
      description: "Led the point-factor evaluation of 380 positions across SEA operations.",
    },
  ],
  // Other employees can have milestones added later
}

/* -------------------------------------------------------------------------- */
/*                                  Page UI                                   */
/* -------------------------------------------------------------------------- */

export default function TalentDossierPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const selectedEmployee = employees.find((e) => e.id === selectedId)

  return (
    <main className="flex flex-col gap-6 p-6 md:flex-row">
      {/* ------------------------------------------------------------------ */}
      {/* Employee List                                                      */}
      {/* ------------------------------------------------------------------ */}
      <section className="w-full space-y-4 md:w-1/2 lg:w-1/3">
        {employees.map((employee) => (
          <Card
            key={employee.id}
            onClick={() => setSelectedId(employee.id)}
            className={`cursor-pointer transition hover:ring-2 hover:ring-primary/50 ${
              selectedId === employee.id ? "ring-2 ring-primary" : ""
            }`}
          >
            <CardHeader className="flex flex-row items-center gap-4">
              <Image
                src={employee.image || "/placeholder.svg"}
                alt={employee.name}
                width={64}
                height={64}
                className="rounded-full object-cover"
              />
              <div>
                <CardTitle className="text-base">{employee.name}</CardTitle>
                <p className="text-sm text-muted-foreground">{employee.role}</p>
              </div>
            </CardHeader>
          </Card>
        ))}
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Dossier Detail                                                     */}
      {/* ------------------------------------------------------------------ */}
      {selectedEmployee && (
        <Card className="flex-1">
          <CardHeader>
            <CardTitle>{selectedEmployee.name}</CardTitle>
            <p className="text-sm text-muted-foreground">{selectedEmployee.role}</p>
          </CardHeader>
          <Separator />
          <CardContent className="space-y-4">
            <div className="flex flex-col gap-1 text-sm">
              <Detail label="Department" value={selectedEmployee.department} />
              <Detail label="Joined" value={selectedEmployee.joined} />
              <Detail label="Reports to" value={selectedEmployee.reportsTo} />
              <Detail label="Team size" value={selectedEmployee.teamSize} />
            </div>

            <Separator />

            <h3 className="font-semibold">Career Milestones</h3>
            <ScrollArea className="h-64 pr-4">
              <ul className="space-y-3">
                {(careerMilestones[selectedEmployee.id] ?? []).map((m) => (
                  <li key={m.date} className="space-y-1">
                    <p className="font-medium">
                      {m.date} – {m.title}
                    </p>
                    <p className="text-sm text-muted-foreground">{m.description}</p>
                  </li>
                ))}
                {careerMilestones[selectedEmployee.id] == null && <p className="text-sm">No milestones recorded.</p>}
              </ul>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </main>
  )
}

/* -------------------------------------------------------------------------- */
/*                               Helper Components                            */
/* -------------------------------------------------------------------------- */

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="min-w-[98px] font-medium">{label}:</span>
      <span>{value}</span>
    </div>
  )
}
