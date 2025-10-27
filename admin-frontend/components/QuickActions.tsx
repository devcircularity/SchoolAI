'use client'

export default function QuickActions({
  onPick,
  disabled,
}: {
  onPick: (text: string) => void | Promise<void>,
  disabled?: boolean
}) {
  const actions: { label: string; prompt: string; desc?: string }[] = [
    { label: 'Create Class', prompt: 'create class P4 East', desc: 'Create a class via Core API' },
    { label: 'Enroll Student', prompt: 'enroll student John Doe admission 123 into P4 East', desc: 'Add a student to a class' },
    { label: 'List Students', prompt: 'list students', desc: 'See all students in your school' },
    { label: 'Create Invoice', prompt: 'create invoice for student 123 amount 15000', desc: 'Issue fees invoice' },
    { label: 'Record Payment', prompt: 'record payment invoice 1 amount 15000', desc: 'Mark invoice paid' },
    { label: 'Help', prompt: 'help', desc: 'Show available commands' },
  ]

  return (
    <div className="grid gap-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {actions.map((a, i) => (
          <button
            key={i}
            className="btn-primary text-sm py-3 px-4 text-left"
            onClick={() => onPick(a.prompt)}
            disabled={disabled}
            title={a.desc}
          >
            <div className="flex flex-col">
              <span className="font-semibold">{a.label}</span>
              {a.desc && <span className="text-xs opacity-80">{a.desc}</span>}
            </div>
          </button>
        ))}
      </div>
      <p className="helper">Make sure you’re logged in so calls include your JWT and <code>X-School-Id</code>.</p>
    </div>
  )
}