-- Pre-populate complaint categories and department mappings
USE college_complaints;

INSERT INTO complaint_categories (name, description, suggested_department) VALUES
('Electrical', 'Issues related to fans, lights, switches, sockets, short circuits, or other electrical appliances.', 'Electrical Maintenance'),
('Plumbing', 'Issues with water taps, leakage, clogged drains, pipes, toilets, or water tanks.', 'Plumbing Maintenance'),
('Classroom', 'Issues inside classrooms such as broken projector, blackboards, screens, podiums, or ACs.', 'Academic Facilities'),
('Hostel', 'Hostel-specific issues like hot water, warden services, room keys, or common area maintenance.', 'Hostel Administration'),
('Internet/Wi-Fi', 'Issues with college Wi-Fi connectivity, LAN ports, login portal, or internet speed.', 'IT & Network Support'),
('Cleaning', 'Request for cleaning or sweeping classrooms, hostels, washrooms, corridors, or trash removal.', 'Housekeeping Services'),
('Furniture', 'Issues with desk repairs, broken chairs, tables, cabinets, cupboards, or doors.', 'Carpentry & Furniture Department'),
('Laboratory', 'Issues inside labs such as non-functional equipment, software errors, or lab bench repairs.', 'Lab Management Support'),
('Transport', 'Issues related to college bus service, scheduling, pass systems, or parking facilities.', 'Transport Department'),
('Other', 'Any general college-related complaint that does not fit into other standard categories.', 'General Administration');
