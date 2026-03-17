"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetBuilder = void 0;
const errors_1 = require("../../errors");
const AddInitialEquipment_1 = require("../Action/AddInitialEquipment");
const BecomeDevout_1 = require("../Action/BecomeDevout");
const ChooseOrigin_1 = require("../Action/ChooseOrigin");
const ChooseRace_1 = require("../Action/ChooseRace");
const ChooseRole_1 = require("../Action/ChooseRole");
const SetInitialAttributes_1 = require("../Action/SetInitialAttributes");
const TrainIntelligenceSkills_1 = require("../Action/TrainIntelligenceSkills");
const Devotion_1 = require("../Devotion/Devotion");
const Inventory_1 = require("../Inventory");
const Origin_1 = require("../Origin");
const Power_1 = require("../Power");
const Race_1 = require("../Race");
const RoleFactory_1 = require("../Role/RoleFactory");
const BuildingSheet_1 = require("./BuildingSheet/BuildingSheet");
const CharacterSheet_1 = require("./CharacterSheet/CharacterSheet");
const Transaction_1 = require("./Transaction");
class SheetBuilder {
    static makeFromSerialized(serialized) {
        var _a;
        const sheetBuilder = new SheetBuilder();
        if (!serialized.race) {
            throw new errors_1.SheetBuilderError('MISSING_RACE');
        }
        if (!serialized.role) {
            throw new errors_1.SheetBuilderError('MISSING_ROLE');
        }
        if (!serialized.origin) {
            throw new errors_1.SheetBuilderError('MISSING_ORIGIN');
        }
        sheetBuilder.setInitialAttributes(serialized.initialAttributes);
        const race = Race_1.RaceFactory.makeFromSerialized(serialized.race);
        sheetBuilder.chooseRace(race);
        const role = RoleFactory_1.RoleFactory.makeFromSerialized(serialized.role);
        sheetBuilder.chooseRole(role);
        const origin = Origin_1.OriginFactory.makeFromSerialized(serialized.origin);
        sheetBuilder.chooseOrigin(origin);
        sheetBuilder.trainIntelligenceSkills(serialized.skills.intelligenceSkills);
        if (serialized.devotion.devotion) {
            const powers = serialized.devotion.devotion.choosedPowers.map(power => Power_1.GrantedPowerFactory.make(power));
            sheetBuilder.addDevotion(new Devotion_1.Devotion(serialized.devotion.devotion.deity, powers));
        }
        if ((_a = serialized.initialEquipment) === null || _a === void 0 ? void 0 : _a.simpleWeapon) {
            const { money, armor, martialWeapon, simpleWeapon } = serialized.initialEquipment;
            sheetBuilder.addInitialEquipment({
                simpleWeapon: Inventory_1.SimpleWeaponFactory.makeFromSerialized(simpleWeapon),
                martialWeapon: martialWeapon
                    ? Inventory_1.MartialWeaponFactory.makeFromSerialized(martialWeapon)
                    : undefined,
                armor: new Inventory_1.LeatherArmor(),
                money,
            });
        }
        return sheetBuilder.build();
    }
    constructor(sheet = new BuildingSheet_1.BuildingSheet()) {
        this.sheet = sheet;
        this.setInitialAttributes = (attributes) => {
            const transaction = new Transaction_1.Transaction(this.sheet);
            transaction.run(new SetInitialAttributes_1.SetInitialAttributes({ transaction, payload: { attributes } }));
            transaction.commit();
            return this;
        };
    }
    getBuildingSheet() {
        return this.sheet;
    }
    reset(sheet = new BuildingSheet_1.BuildingSheet()) {
        this.sheet = sheet;
        return this;
    }
    chooseRace(race) {
        const transaction = new Transaction_1.Transaction(this.sheet);
        transaction.run(new ChooseRace_1.ChooseRace({ payload: { race }, transaction }));
        transaction.commit();
        return this;
    }
    chooseRole(role) {
        const transaction = new Transaction_1.Transaction(this.sheet);
        transaction.run(new ChooseRole_1.ChooseRole({ transaction, payload: { role } }));
        transaction.commit();
        return this;
    }
    chooseOrigin(origin) {
        const transaction = new Transaction_1.Transaction(this.sheet);
        transaction.run(new ChooseOrigin_1.ChooseOrigin({ payload: { origin }, transaction }));
        transaction.commit();
        return this;
    }
    trainIntelligenceSkills(skills) {
        const transaction = new Transaction_1.Transaction(this.sheet);
        transaction.run(new TrainIntelligenceSkills_1.TrainIntelligenceSkills({ payload: { skills }, transaction }));
        transaction.commit();
        return this;
    }
    addInitialEquipment(params) {
        const transaction = new Transaction_1.Transaction(this.sheet);
        const sheetRole = this.sheet.getSheetRole();
        const role = sheetRole.getRole();
        if (!role) {
            throw new errors_1.SheetBuilderError('REQUIRED_ROLE_FOR_INITIAL_EQUIPMENT');
        }
        transaction.run(new AddInitialEquipment_1.AddInitialEquipment({
            payload: Object.assign(Object.assign({}, params), { role }),
            transaction,
        }));
        transaction.commit();
        return this;
    }
    addDevotion(devotion) {
        const transaction = new Transaction_1.Transaction(this.sheet);
        transaction.run(new BecomeDevout_1.BecomeDevout({
            payload: {
                devotion,
            },
            transaction,
        }));
        transaction.commit();
        return this;
    }
    build() {
        const powers = this.sheet.getSheetPowers();
        powers.getGeneralPowers().forEach(power => {
            power.verifyRequirements(this.sheet);
        });
        powers.getOriginPowers().forEach(power => {
            power.verifyRequirements(this.sheet);
        });
        powers.getRolePowers().forEach(power => {
            power.verifyRequirements(this.sheet);
        });
        return this.createSheet();
    }
    createSheet() {
        const race = this.sheet.getSheetRace().getRace();
        const role = this.sheet.getSheetRole().getRole();
        const origin = this.sheet.getSheetOrigin().getOrigin();
        if (!race) {
            throw new errors_1.SheetBuilderError('REQUIRED_RACE');
        }
        if (!role) {
            throw new errors_1.SheetBuilderError('REQUIRED_ROLE');
        }
        if (!origin) {
            throw new errors_1.SheetBuilderError('REQUIRED_ORIGIN');
        }
        return new CharacterSheet_1.CharacterSheet({
            race,
            role,
            origin,
            abilities: this.sheet.getSheetAbilities(),
            attributes: this.sheet.getSheetAttributes(),
            buildSteps: this.sheet.getBuildSteps(),
            defense: this.sheet.getSheetDefense(),
            displacement: this.sheet.getSheetDisplacement(),
            inventory: this.sheet.getSheetInventory(),
            level: this.sheet.getLevel(),
            lifePoints: this.sheet.getSheetLifePoints(),
            manaPoints: this.sheet.getSheetManaPoints(),
            powers: this.sheet.getSheetPowers(),
            proficiencies: this.sheet.getSheetProficiencies(),
            skills: this.sheet.getSheetSkills(),
            spells: this.sheet.getSheetSpells(),
            vision: this.sheet.getSheetVision(),
            size: this.sheet.getSheetSize(),
            devotion: this.sheet.getSheetDevotion(),
            sheetResistences: this.sheet.getSheetResistences(),
            sheetTriggeredEffects: this.sheet.getSheetTriggeredEffects(),
            activateableEffects: this.sheet.getSheetActivateableEffects(),
        });
    }
}
exports.SheetBuilder = SheetBuilder;
