"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Context_1 = require("../Context");
const DiceRoll_1 = require("../Dice/DiceRoll");
const Sheet_1 = require("../Sheet");
const SheetAttributes_1 = require("../Sheet/SheetAttributes");
const Skill_1 = require("../Skill");
const SheetSkill_1 = require("../Skill/SheetSkill");
const Skill_2 = require("../Skill/Skill");
const SkillTotalCalculatorFactory_1 = require("../Skill/SkillTotalCalculatorFactory");
const Attack_1 = require("./Attack");
const Critical_1 = require("./Critical");
describe('Attack', () => {
    let attackSkill;
    beforeAll(() => {
        attackSkill = new SheetSkill_1.SheetSkill(new Skill_2.Skill({ attribute: 'strength', isTrained: false, name: Skill_1.SkillName.fight }), SkillTotalCalculatorFactory_1.SkillTotalCalculatorFactory.make(SheetAttributes_1.SheetAttributes.initial, Sheet_1.Level.one, new Context_1.OutOfGameContext()));
    });
    it('should calculate regular roll result', () => {
        const damage = new DiceRoll_1.DiceRoll(1, 6);
        const critical = new Critical_1.Critical(20, 2);
        const attack = new Attack_1.Attack(damage, critical, 'default');
        const fakeRandom = { get: vi.fn(() => 1) };
        const result = attack.roll(fakeRandom, attackSkill);
        expect(result.damage.rolls).toEqual([1]);
        expect(result.damage.discartedRolls).toEqual([]);
        expect(result.damage.total).toEqual(1);
    });
    it('should calculate critical roll 20/x2', () => {
        const damage = new DiceRoll_1.DiceRoll(1, 6);
        const critical = new Critical_1.Critical(20, 2);
        const attack = new Attack_1.Attack(damage, critical, 'default');
        const fakeRandom = { get: vi.fn().mockReturnValueOnce(20).mockReturnValue(1) };
        const result = attack.roll(fakeRandom, attackSkill);
        expect(result.damage.rolls).toEqual([1, 1]);
        expect(result.damage.discartedRolls).toEqual([]);
        expect(result.damage.total).toEqual(2);
    });
    it('should calculate critical roll 19/x3', () => {
        const damage = new DiceRoll_1.DiceRoll(1, 6);
        const critical = new Critical_1.Critical(19, 3);
        const attack = new Attack_1.Attack(damage, critical, 'default');
        const fakeRandom = { get: vi.fn().mockReturnValueOnce(19).mockReturnValue(1) };
        const result = attack.roll(fakeRandom, attackSkill);
        expect(result.damage.rolls).toEqual([1, 1, 1]);
        expect(result.damage.discartedRolls).toEqual([]);
        expect(result.damage.total).toEqual(3);
        expect(result.test.total).toEqual(19);
    });
});
