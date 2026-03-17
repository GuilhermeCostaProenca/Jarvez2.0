"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const EquipmentName_1 = require("../../Inventory/Equipment/EquipmentName");
const Power_1 = require("../../Power");
const IronWill_1 = require("../../Power/GeneralPower/DestinyPower/IronWill/IronWill");
const Medicine_1 = require("../../Power/GeneralPower/DestinyPower/Medicine/Medicine");
const ChurchMember_1 = require("../../Power/OriginPower/ChurchMember");
const Sheet_1 = require("../../Sheet");
const Transaction_1 = require("../../Sheet/Transaction");
const SkillName_1 = require("../../Skill/SkillName");
const OriginBenefitGeneralPower_1 = require("../OriginBenefit/OriginBenefitGeneralPower");
const OriginBenefitOriginPower_1 = require("../OriginBenefit/OriginBenefitOriginPower");
const OriginBenefitSkill_1 = require("../OriginBenefit/OriginBenefitSkill");
const Acolyte_1 = require("./Acolyte");
describe('Acolyte', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should dispatch add items', () => {
        const acolyte = new Acolyte_1.Acolyte([new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.cure), new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.religion)]);
        const sheet = new Sheet_1.BuildingSheet();
        const transaction = new Transaction_1.Transaction(sheet);
        acolyte.addToSheet(transaction);
        expect(sheet.getSheetInventory().getEquipment(EquipmentName_1.EquipmentName.sacredSymbol)).toBeDefined();
        expect(sheet.getSheetInventory().getEquipment(EquipmentName_1.EquipmentName.priestCostume)).toBeDefined();
    });
    it('should dispatch skill benefits training', () => {
        const acolyte = new Acolyte_1.Acolyte([new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.cure), new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.religion)]);
        acolyte.addToSheet(transaction);
        const firstSkill = sheet.getSkills()[SkillName_1.SkillName.cure].skill;
        const secondSkill = sheet.getSkills()[SkillName_1.SkillName.religion].skill;
        expect(firstSkill.getIsTrained()).toBe(true);
        expect(secondSkill.getIsTrained()).toBe(true);
    });
    it('should not allow not listed skills', () => {
        expect(() => {
            const acolyte = new Acolyte_1.Acolyte([new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.cure), new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.aim)]);
        }).toThrow('INVALID_ORIGIN_SKILL');
    });
    it('should not allow more than two benefits', () => {
        expect(() => {
            const acolyte = new Acolyte_1.Acolyte([new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.cure), new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.cure), new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.will)]);
        }).toThrow('INVALID_ORIGIN_BENEFITS');
    });
    it('should not allow less than two benefits', () => {
        expect(() => {
            const acolyte = new Acolyte_1.Acolyte([new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.cure)]);
        }).toThrow('INVALID_ORIGIN_BENEFITS');
    });
    it('should dispatch general power benefits appliance', () => {
        const acolyte = new Acolyte_1.Acolyte([new OriginBenefitGeneralPower_1.OriginBenefitGeneralPower(new IronWill_1.IronWill()), new OriginBenefitGeneralPower_1.OriginBenefitGeneralPower(new Medicine_1.Medicine())]);
        acolyte.addToSheet(transaction);
        const powers = sheet.getSheetPowers().getGeneralPowers();
        expect(powers.get(Power_1.GeneralPowerName.ironWill)).toBeDefined();
        expect(powers.get(Power_1.GeneralPowerName.medicine)).toBeDefined();
    });
    it('should dispatch origin power as benefit appliance', () => {
        const acolyte = new Acolyte_1.Acolyte([new OriginBenefitOriginPower_1.OriginBenefitOriginPower(new ChurchMember_1.ChurchMember()), new OriginBenefitGeneralPower_1.OriginBenefitGeneralPower(new Medicine_1.Medicine())]);
        acolyte.addToSheet(transaction);
        const originPowers = sheet.getSheetPowers().getOriginPowers();
        const generalPowers = sheet.getSheetPowers().getGeneralPowers();
        expect(originPowers.get(Power_1.OriginPowerName.churchMember)).toBeDefined();
        expect(generalPowers.get(Power_1.GeneralPowerName.medicine)).toBeDefined();
    });
});
