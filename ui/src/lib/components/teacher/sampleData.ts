// Illustrative placeholder data for the teacher-section design prototype.
// There is no classrooms backend yet — these arrays only exist to convey the
// intended *populated* look of each section, and will be replaced by real API data.

export interface SampleClass {
	id: string;
	name: string;
	subject: string;
	level: string;
	students: number;
	activeToday: number;
}

export interface SampleStudent {
	id: string;
	name: string;
	classes: string[];
	status: 'active' | 'idle' | 'not_started';
	lastActive: string;
	supports: number;
	guardians: 'linked' | 'pending' | 'none';
}

export interface SampleResource {
	id: string;
	name: string;
	klass: string;
	type: string;
	size: string;
	uploaded: string;
}

export interface SampleTemplate {
	id: string;
	title: string;
	updated: string;
}

export const sampleClasses: SampleClass[] = [
	{
		id: 'math-6',
		name: 'Math · Grade 6',
		subject: 'Mathematics',
		level: 'Grade 6',
		students: 18,
		activeToday: 4
	},
	{
		id: 'phys-5',
		name: 'Physics · Grade 5',
		subject: 'Physics',
		level: 'Grade 5',
		students: 15,
		activeToday: 2
	},
	{
		id: 'bio-4',
		name: 'Biology · Grade 4',
		subject: 'Biology',
		level: 'Grade 4',
		students: 14,
		activeToday: 3
	}
];

export const sampleStudents: SampleStudent[] = [
	{
		id: 's1',
		name: 'Sara Amrani',
		classes: ['Math · G6'],
		status: 'active',
		lastActive: '2h ago',
		supports: 6,
		guardians: 'linked'
	},
	{
		id: 's2',
		name: 'Omar Benali',
		classes: ['Math · G6', 'Physics · G5'],
		status: 'idle',
		lastActive: '5d ago',
		supports: 3,
		guardians: 'pending'
	},
	{
		id: 's3',
		name: 'Lina Cherkaoui',
		classes: ['Biology · G4'],
		status: 'not_started',
		lastActive: '—',
		supports: 0,
		guardians: 'none'
	},
	{
		id: 's4',
		name: 'Zaid Daoudi',
		classes: ['Physics · G5'],
		status: 'active',
		lastActive: '1d ago',
		supports: 4,
		guardians: 'linked'
	}
];

export const sampleResources: SampleResource[] = [
	{
		id: 'r1',
		name: 'Fractions worksheet.pdf',
		klass: 'Math · G6',
		type: 'PDF',
		size: '1.2 MB',
		uploaded: 'Jun 09'
	},
	{
		id: 'r2',
		name: 'Lab safety.docx',
		klass: 'Physics · G5',
		type: 'DOC',
		size: '340 KB',
		uploaded: 'Jun 05'
	}
];

export const sampleTemplates: SampleTemplate[] = [
	{ id: 't1', title: 'Weekly quiz', updated: 'Jun 08' },
	{ id: 't2', title: 'Reading log', updated: 'May 30' }
];
