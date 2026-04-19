BEGIN;

-- Stakeholders

INSERT INTO stakeholders (id, name, role) VALUES

-- COFFEE CHAIN
(1, 'Green Valley Farm', 'farmer'),
(2, 'Hilltop Coffee Farm', 'farmer'),
(3, 'Coffee Processors Ltd', 'processor'),
(4, 'Global Coffee Distributors', 'distributor'),
(5, 'City Coffee Retail', 'retailer'),

-- COCOA CHAIN
(6, 'Cocoa Farms West', 'farmer'),
(7, 'Rainforest Cocoa Ltd', 'farmer'),
(8, 'Cocoa Processing Hub', 'processor'),
(9, 'Chocolate Distributors Inc', 'distributor'),
(10, 'Sweet Retail Store', 'retailer'),

-- COTTON CHAIN
(11, 'Cotton Growers Union', 'farmer'),
(12, 'Organic Cotton Farm', 'farmer'),
(13, 'Textile Processing Ltd', 'processor'),
(14, 'Fabric Distributors', 'distributor'),
(15, 'Clothing Retail Hub', 'retailer'),

-- EDGE CASES (kept for demo, not used in batches)
(16, 'Expired Farm', 'farmer'),               -- will receive an EXPIRED certification
(17, 'Uncertified Retailer', 'retailer'),     -- no certification at all
(18, 'Revoked Distributor', 'distributor');   -- will receive a REVOKED (is_active=FALSE) certification


-- Certifications

INSERT INTO certifications (stakeholder_id, certifying_body, issue_date, expiry_date, is_active) VALUES

-- COFFEE
(1, 'FairTrade', '2025-01-01', '2030-01-01', TRUE),
(2, 'Organic', '2025-01-01', '2030-01-01', TRUE),
(3, 'Food Safety', '2025-01-01', '2030-01-01', TRUE),
(4, 'Export Cert', '2025-01-01', '2030-01-01', TRUE),
(5, 'Retail Cert', '2025-01-01', '2030-01-01', TRUE),

-- COCOA
(6, 'FairTrade', '2025-01-01', '2030-01-01', TRUE),
(7, 'Organic', '2025-01-01', '2030-01-01', TRUE),
(8, 'Processing Cert', '2025-01-01', '2030-01-01', TRUE),
(9, 'Export Cert', '2025-01-01', '2030-01-01', TRUE),
(10, 'Retail Cert', '2025-01-01', '2030-01-01', TRUE),

-- COTTON
(11, 'Organic Cotton', '2025-01-01', '2030-01-01', TRUE),
(12, 'Eco Cert', '2025-01-01', '2030-01-01', TRUE),
(13, 'Textile Cert', '2025-01-01', '2030-01-01', TRUE),
(14, 'Distribution Cert', '2025-01-01', '2030-01-01', TRUE),
(15, 'Retail Cert', '2025-01-01', '2030-01-01', TRUE),

-- EDGE CASE CERTS
(16, 'FairTrade',    '2018-01-01', '2020-01-01', TRUE),    -- EXPIRED certification
(18, 'Export Cert',  '2025-01-01', '2030-01-01', FALSE);   -- REVOKED (is_active = FALSE)


-- Batches

-- COFFEE
INSERT INTO batches (id, product_name, quantity, unit, current_owner_id) VALUES
(100, 'Coffee Raw A', 1000, 'kg', 1),
(101, 'Coffee Raw B', 800, 'kg', 2),
(102, 'Coffee Proc A1', 600, 'kg', 3),
(103, 'Coffee Proc A2', 400, 'kg', 3),
(104, 'Coffee Proc B1', 800, 'kg', 3),
(105, 'Coffee Export', 1800, 'kg', 4),
(106, 'Coffee Retail 1', 900, 'kg', 5),
(107, 'Coffee Retail 2', 900, 'kg', 5);

-- COCOA
INSERT INTO batches (id, product_name, quantity, unit, current_owner_id) VALUES
(200, 'Cocoa Raw A', 900, 'kg', 6),
(201, 'Cocoa Raw B', 700, 'kg', 7),
(202, 'Cocoa Proc A1', 500, 'kg', 8),
(203, 'Cocoa Proc A2', 400, 'kg', 8),
(204, 'Cocoa Proc B1', 700, 'kg', 8),
(205, 'Cocoa Export', 1600, 'kg', 9),
(206, 'Chocolate Batch 1', 800, 'kg', 10),
(207, 'Chocolate Batch 2', 800, 'kg', 10);

-- COTTON
INSERT INTO batches (id, product_name, quantity, unit, current_owner_id) VALUES
(300, 'Cotton Raw A', 1200, 'kg', 11),
(301, 'Cotton Raw B', 900, 'kg', 12),
(302, 'Cotton Proc A1', 700, 'kg', 13),
(303, 'Cotton Proc A2', 500, 'kg', 13),
(304, 'Cotton Proc B1', 900, 'kg', 13),
(305, 'Fabric Export', 2100, 'kg', 14),
(306, 'Clothing Batch 1', 1000, 'kg', 15),
(307, 'Clothing Batch 2', 1100, 'kg', 15);


-- Batch Relations

-- COFFEE
INSERT INTO batch_relations VALUES
(100, 102), (100, 103),
(101, 104),
(102, 105), (103, 105), (104, 105),
(105, 106), (105, 107);

-- COCOA
INSERT INTO batch_relations VALUES
(200, 202), (200, 203),
(201, 204),
(202, 205), (203, 205), (204, 205),
(205, 206), (205, 207);

-- COTTON
INSERT INTO batch_relations VALUES
(300, 302), (300, 303),
(301, 304),
(302, 305), (303, 305), (304, 305),
(305, 306), (305, 307);

-- Synchronize the serial sequences with the explicitly inserted IDs
SELECT setval('stakeholders_id_seq', (SELECT MAX(id) FROM stakeholders));
SELECT setval('batches_id_seq',      (SELECT MAX(id) FROM batches));

COMMIT;
