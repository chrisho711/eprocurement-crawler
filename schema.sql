CREATE DATABASE `TW_PROCUREMENT` /*!40100 DEFAULT CHARACTER SET utf8 */;

CREATE TABLE `organization_info` (
  `pk_atm_main` varchar(45) NOT NULL COMMENT '採購網主鍵',
  `tender_case_no` varchar(45) NOT NULL COMMENT '標案案號',
  `org_id` varchar(45) DEFAULT NULL COMMENT '機關代碼',
  `org_name` varchar(45) DEFAULT NULL COMMENT '機關名稱',
  `unit_name` varchar(50) DEFAULT NULL COMMENT '單位名稱',
  `org_address` varchar(100) DEFAULT NULL COMMENT '機關地址',
  `contact` varchar(45) DEFAULT NULL COMMENT '聯絡人',
  `tel` varchar(45) DEFAULT NULL COMMENT '聯絡電話',
  `fax` varchar(45) DEFAULT NULL COMMENT '傳真號碼',
  PRIMARY KEY (`pk_atm_main`,`tender_case_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `procurement_info` (
  `pk_atm_main` varchar(45) NOT NULL COMMENT '採購網主鍵',
  `tender_case_no` varchar(45) NOT NULL COMMENT '標案案號',
  `procurement_type` varchar(45) DEFAULT NULL COMMENT '招標方式',
  `awarding_type` varchar(45) DEFAULT NULL COMMENT '決標方式',
  `is_follow_law_64_2` char(1) DEFAULT NULL COMMENT '是否依政府採購法施行細則第64條之2辦理',
  `num_transmit` varchar(45) DEFAULT NULL COMMENT '新增公告傳輸次數',
  `revision_sn` varchar(10) DEFAULT NULL COMMENT '公告更正序號',
  `is_follow_law_106_1_1` char(1) DEFAULT NULL COMMENT '是否依據採購法第106條第1項第1款辦理',
  `subject_of_procurement` varchar(100) DEFAULT NULL COMMENT '標案名稱',
  `attr_of_awarding` varchar(45) DEFAULT NULL COMMENT '決標資料類別',
  `is_inter_entity_supply_contract` char(1) DEFAULT NULL COMMENT '是否屬共同供應契約採購',
  `is_joint_procurement` char(1) DEFAULT NULL COMMENT '是否屬二以上機關之聯合採購(不適用共同供應契約規定)',
  `is_multiple_award` char(1) DEFAULT NULL COMMENT '是否複數決標',
  `is_joint_tender` char(1) DEFAULT NULL COMMENT '是否共同投標',
  `attr_of_procurement` varchar(45) DEFAULT NULL COMMENT '標的分類',
  `is_design_build_contract` char(1) DEFAULT NULL COMMENT '是否屬統包',
  `is_engineer_certification_required` char(1) DEFAULT NULL COMMENT '是否應依公共工程專業技師簽證規則實施技師簽證',
  `opening_date` datetime DEFAULT NULL COMMENT '開標時間',
  `original_publication_date` date DEFAULT NULL COMMENT '原公告日期',
  `procurement_money_amount_level` varchar(45) DEFAULT NULL COMMENT '採購金額級距',
  `conduct_procurement` varchar(10) DEFAULT NULL COMMENT '辦理方式',
  `is_gpa` varchar(45) DEFAULT NULL COMMENT '是否適用WTO政府採購協定(GPA)：',
  `is_anztec` varchar(45) DEFAULT NULL COMMENT '是否適用臺紐經濟合作協定(ANZTEC)：',
  `is_astep` varchar(45) DEFAULT NULL COMMENT '是否適用臺星經濟夥伴協定(ASTEP)：',
  `restricted_tendering_law` varchar(100) DEFAULT NULL COMMENT '限制性招標依據之法條',
  `is_budget_amount_public` char(1) DEFAULT NULL COMMENT '預算金額是否公開',
  `budget_amount` decimal(10,0) DEFAULT NULL COMMENT '預算金額',
  `is_org_subsidy` char(1) DEFAULT NULL COMMENT '是否受機關補助',
  `fulfill_location` varchar(100) DEFAULT NULL COMMENT '履約地點',
  `fulfill_location_district` varchar(45) DEFAULT NULL COMMENT '履約地點（含地區）',
  `is_special_budget` char(1) DEFAULT NULL COMMENT '是否含特別預算',
  `project_type` varchar(45) DEFAULT NULL COMMENT '歸屬計畫類別',
  `is_authorities_template` char(1) DEFAULT NULL COMMENT '本案採購契約是否採用主管機關訂定之範本',
  PRIMARY KEY (`pk_atm_main`,`tender_case_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `tender_info` (
  `pk_atm_main` varchar(45) NOT NULL COMMENT '採購網主鍵',
  `tender_case_no` varchar(45) NOT NULL COMMENT '標案案號',
  `tender_sn` int(11) NOT NULL COMMENT '廠商流水號',
  `tenderer_id` varchar(45) DEFAULT NULL COMMENT '廠商代碼',
  `tenderer_name` varchar(45) DEFAULT NULL COMMENT '廠商名稱',
  `tenderer_name_eng` varchar(100) DEFAULT NULL COMMENT '廠商名稱(英)',
  `is_awarded` char(1) DEFAULT NULL COMMENT '是否得標',
  `organization_type` varchar(45) DEFAULT NULL COMMENT '組織型態',
  `industry_type` varchar(45) DEFAULT NULL COMMENT '廠商業別',
  `address` varchar(100) DEFAULT NULL COMMENT '廠商地址',
  `address_eng` varchar(200) DEFAULT NULL COMMENT '廠商地址(英)',
  `tel` varchar(45) DEFAULT NULL COMMENT '廠商電話',
  `award_price` decimal(10,0) DEFAULT NULL COMMENT '決標金額',
  `country` varchar(45) DEFAULT NULL COMMENT '得標廠商國別',
  `is_sm_enterprise` char(1) DEFAULT NULL COMMENT '是否為中小企業',
  `fulfill_date_start` date DEFAULT NULL COMMENT '履約起日',
  `fulfill_date_end` date DEFAULT NULL COMMENT '履約迄日',
  `is_employee_over_100` char(1) DEFAULT NULL COMMENT '雇用員工總人數是否超過100人',
  `num_employee` int(11) DEFAULT NULL COMMENT '僱用員工總人數',
  `num_aboriginal` int(11) DEFAULT NULL COMMENT '已僱用原住民人數',
  `num_disability` int(11) DEFAULT NULL COMMENT '已僱用身心障礙者人數',
  PRIMARY KEY (`pk_atm_main`,`tender_case_no`,`tender_sn`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `tender_award_item` (
  `pk_atm_main` varchar(45) NOT NULL COMMENT '採購網主鍵',
  `tender_case_no` varchar(45) NOT NULL COMMENT '標案案號',
  `item_sn` int(11) NOT NULL COMMENT '品項流水號',
  `tender_sn` int(11) NOT NULL COMMENT '廠商流水號',
  `item_name` varchar(100) DEFAULT NULL COMMENT '品項名稱',
  `unit` varchar(20) DEFAULT NULL COMMENT '單位',
  `is_unit_price_x_qty_lowest` char(1) DEFAULT NULL COMMENT '是否以單價及預估需求數量之乘積決定最低標',
  `awarded_tenderer` varchar(100) DEFAULT NULL COMMENT '得標廠商',
  `request_number` int(11) DEFAULT NULL COMMENT '預估需求數量',
  `award_price` decimal(10,0) DEFAULT NULL COMMENT '決標金額',
  `base_price` decimal(10,0) DEFAULT NULL COMMENT '底價金額',
  `source_country` varchar(100) DEFAULT NULL COMMENT '原產地國別',
  `source_award_price` decimal(10,0) DEFAULT NULL COMMENT '原產地國別得標金額',
  PRIMARY KEY (`pk_atm_main`,`tender_case_no`,`item_sn`,`tender_sn`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `evaluation_committee_info` (
  `pk_atm_main` varchar(45) NOT NULL COMMENT '採購網主鍵',
  `tender_case_no` varchar(45) NOT NULL COMMENT '標案案號',
  `sn` int(11) NOT NULL COMMENT '項次',
  `is_attend` char(1) DEFAULT NULL COMMENT '出席會議',
  `name` varchar(45) DEFAULT NULL COMMENT '姓名',
  `occupation` varchar(45) DEFAULT NULL COMMENT '職業',
  PRIMARY KEY (`pk_atm_main`,`tender_case_no`,`sn`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `award_info` (
  `pk_atm_main` varchar(45) NOT NULL COMMENT '採購網主鍵',
  `tender_case_no` varchar(45) NOT NULL COMMENT '標案案號',
  `award_announce_sn` varchar(10) DEFAULT NULL COMMENT '決標公告序號',
  `revision_sn` varchar(10) DEFAULT NULL COMMENT '公告更正序號',
  `awarding_date` date DEFAULT NULL COMMENT '決標日期',
  `original_awarding_announce_date` date DEFAULT NULL COMMENT '原決標公告日期',
  `awarding_announce_date` date DEFAULT NULL COMMENT '決標公告日期',
  `is_post_bulletin` char(1) DEFAULT NULL COMMENT '是否刊登公報',
  `base_price` decimal(10,0) DEFAULT NULL COMMENT '底價金額',
  `is_base_price_public` char(1) DEFAULT NULL COMMENT '底價金額是否公開',
  `total_award_price` decimal(10,0) DEFAULT NULL COMMENT '總決標金額',
  `is_total_award_price_public` char(1) DEFAULT NULL COMMENT '總決標金額是否公開',
  `is_price_dynamic_with_cpi` char(1) DEFAULT NULL COMMENT '契約是否訂有依物價指數調整價金規定',
  `no_price_dynamic_description` varchar(100) DEFAULT NULL COMMENT '未列物價調整規定說明',
  `fulfill_execution_org_id` varchar(45) DEFAULT NULL COMMENT '履約執行機關代碼',
  `fulfill_execution_org_name` varchar(100) DEFAULT NULL COMMENT '履約執行機關名稱',
  `additional_info` varchar(200) DEFAULT NULL COMMENT '附加說明',
  PRIMARY KEY (`pk_atm_main`,`tender_case_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
