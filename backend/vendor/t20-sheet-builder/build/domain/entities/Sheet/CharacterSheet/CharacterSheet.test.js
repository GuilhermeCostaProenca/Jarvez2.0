"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Deities_1 = require("../../Devotion/Deities");
const DeityName_1 = require("../../Devotion/DeityName");
const Devotion_1 = require("../../Devotion/Devotion");
const EquipmentName_1 = require("../../Inventory/Equipment/EquipmentName");
const LeatherArmor_1 = require("../../Inventory/Equipment/Weapon/DefensiveWeapon/Armor/LightArmor/LeatherArmor");
const LongSword_1 = require("../../Inventory/Equipment/Weapon/OffensiveWeapon/MartialWeapon/LongSword");
const Dagger_1 = require("../../Inventory/Equipment/Weapon/OffensiveWeapon/SimpleWeapon/Dagger");
const Acolyte_1 = require("../../Origin/Acolyte/Acolyte");
const AnimalsFriend_1 = require("../../Origin/AnimalsFriend/AnimalsFriend");
const OriginBenefitGeneralPower_1 = require("../../Origin/OriginBenefit/OriginBenefitGeneralPower");
const OriginBenefitOriginPower_1 = require("../../Origin/OriginBenefit/OriginBenefitOriginPower");
const OriginBenefitSkill_1 = require("../../Origin/OriginBenefit/OriginBenefitSkill");
const Power_1 = require("../../Power");
const IronWill_1 = require("../../Power/GeneralPower/DestinyPower/IronWill/IronWill");
const GeneralPowerName_1 = require("../../Power/GeneralPower/GeneralPowerName");
const AnalyticMind_1 = require("../../Power/GrantedPower/AnalyticMind/AnalyticMind");
const EmptyMind_1 = require("../../Power/GrantedPower/EmptyMind/EmptyMind");
const GrantedPowerName_1 = require("../../Power/GrantedPower/GrantedPowerName");
const SpecialFriend_1 = require("../../Power/OriginPower/SpecialFriend");
const Dwarf_1 = require("../../Race/Dwarf/Dwarf");
const Human_1 = require("../../Race/Human/Human");
const VersatileChoicePower_1 = require("../../Race/Human/Versatile/VersatileChoicePower");
const VersatileChoiceSkill_1 = require("../../Race/Human/Versatile/VersatileChoiceSkill");
const ArcanistBuider_1 = require("../../Role/Arcanist/ArcanistBuider");
const ArcanistPathMage_1 = require("../../Role/Arcanist/ArcanistPath/ArcanistPathMage/ArcanistPathMage");
const RoleAbilityName_1 = require("../../Role/RoleAbilityName");
const Warrior_1 = require("../../Role/Warrior/Warrior");
const SkillName_1 = require("../../Skill/SkillName");
const ArcaneArmor_1 = require("../../Spell/ArcaneArmor/ArcaneArmor");
const FlamesExplosion_1 = require("../../Spell/FlamesExplosion/FlamesExplosion");
const IllusoryDisguise_1 = require("../../Spell/IllusoryDisguise/IllusoryDisguise");
const MentalDagger_1 = require("../../Spell/MentalDagger/MentalDagger");
const Proficiency_1 = require("../Proficiency");
const SheetBuilder_1 = require("../SheetBuilder");
const Vision_1 = require("../Vision");
describe('Sheet', () => {
    describe('Human Warrior', () => {
        let sheet;
        let role;
        let race;
        let sheetBuilder;
        let origin;
        beforeAll(() => {
            const choices = [
                new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics),
                new VersatileChoicePower_1.VersatileChoicePower(new Power_1.OneWeaponStyle()),
            ];
            race = new Human_1.Human(['charisma', 'constitution', 'dexterity'], choices);
            role = new Warrior_1.Warrior([[SkillName_1.SkillName.fight], [SkillName_1.SkillName.aim, SkillName_1.SkillName.athletics]]);
            sheetBuilder = new SheetBuilder_1.SheetBuilder();
            origin = new Acolyte_1.Acolyte([new OriginBenefitGeneralPower_1.OriginBenefitGeneralPower(new IronWill_1.IronWill()), new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.cure)]);
            sheet = sheetBuilder
                .setInitialAttributes({ strength: 0, dexterity: 0, charisma: 0, constitution: 0, intelligence: 0, wisdom: 2 })
                .chooseRace(race)
                .chooseRole(role)
                .chooseOrigin(origin)
                .trainIntelligenceSkills([])
                .addInitialEquipment({
                simpleWeapon: new Dagger_1.Dagger(),
                armor: new LeatherArmor_1.LeatherArmor(),
                martialWeapon: new LongSword_1.LongSword(),
                money: 24,
            })
                .build();
        });
        it('should choose race', () => {
            expect(sheet.getSheetRace().getRace()).toBe(race);
        });
        it('should have displacement 9', () => {
            expect(sheet.getSheetDisplacement().getDisplacement()).toBe(9);
        });
        it('should have default vision', () => {
            expect(sheet.getSheetVision().getVision()).toBe(Vision_1.Vision.default);
        });
        it('should have versatile power', () => {
            const powers = sheet.getSheetPowers();
            expect(powers.getGeneralPowers().has(GeneralPowerName_1.GeneralPowerName.oneWeaponStyle)).toBeTruthy();
        });
        it('should have versatile skill trained', () => {
            const skills = sheet.getSheetSkills().getSkills();
            expect(skills.acrobatics.getIsTrained()).toBeTruthy();
        });
        it('should choose role', () => {
            expect(sheet.getSheetRole().getRole()).toBe(role);
        });
        it('should have initial role life points + constitution', () => {
            expect(sheet.getMaxLifePoints()).toBe(21);
        });
        it('should have role skills trained', () => {
            const skills = sheet.getSheetSkills().getSkills();
            expect(skills.fight.getIsTrained()).toBeTruthy();
            expect(skills.aim.getIsTrained()).toBeTruthy();
            expect(skills.fortitude.getIsTrained()).toBeTruthy();
            expect(skills.athletics.getIsTrained()).toBeTruthy();
        });
        it('should have role abilities', () => {
            const abilities = sheet.getSheetAbilities();
            expect(abilities.getRoleAbilities().has(RoleAbilityName_1.RoleAbilityName.specialAttack)).toBeTruthy();
        });
        it('should have origin power', () => {
            const powers = sheet.getSheetPowers();
            expect(powers.getGeneralPowers().has(GeneralPowerName_1.GeneralPowerName.ironWill)).toBeTruthy();
        });
        it('should have origin skill trained', () => {
            const skills = sheet.getSheetSkills().getSkills();
            expect(skills.cure.getIsTrained()).toBeTruthy();
        });
        it('should have origin equipments', () => {
            expect(sheet.getSheetInventory().getEquipments().has(EquipmentName_1.EquipmentName.priestCostume)).toBeTruthy();
            expect(sheet.getSheetInventory().getEquipments().has(EquipmentName_1.EquipmentName.sacredSymbol)).toBeTruthy();
        });
        it('should have default initial equipments.has(', () => {
            expect(sheet.getSheetInventory().getEquipments().has(EquipmentName_1.EquipmentName.backpack)).toBeTruthy();
            expect(sheet.getSheetInventory().getEquipments().has(EquipmentName_1.EquipmentName.sleepingBag)).toBeTruthy();
            expect(sheet.getSheetInventory().getEquipments().has(EquipmentName_1.EquipmentName.travelerCostume)).toBeTruthy();
        });
        it('should have chosen weapon', () => {
            expect(sheet.getSheetInventory().getEquipments().has(EquipmentName_1.EquipmentName.dagger)).toBeTruthy();
        });
        it('should have chosen martial weapon', () => {
            expect(sheet.getSheetInventory().getEquipments().has(EquipmentName_1.EquipmentName.longSword)).toBeTruthy();
        });
        it('should have chosen armor', () => {
            const armor = sheet.getSheetInventory().getEquipments().get(EquipmentName_1.EquipmentName.leatherArmor);
            expect(armor).toBeTruthy();
        });
        it('should receive a light shield', () => {
            const shield = sheet.getSheetInventory().getEquipments().get(EquipmentName_1.EquipmentName.lightShield);
            expect(shield).toBeTruthy();
        });
        it('should have initial money', () => {
            expect(sheet.getSheetInventory().getMoney()).toBe(24);
        });
        it('should have medium size', () => {
            expect(sheet.getSheetSize().getSize()).toBe('medium');
            expect(sheet.getSheetSize().getOccupiedSpaceInMeters()).toBe(1.5);
            expect(sheet.getSheetSize().getManeuversModifier()).toBe(0);
            expect(sheet.getSheetSize().getFurtivityModifier()).toBe(0);
        });
        it('should not be devout', () => {
            expect(sheet.getSheetDevotion().isDevout()).toBeFalsy();
        });
        it('should receive 1 granted power if devout', () => {
            expect(sheet.getSheetDevotion().getGrantedPowerCount()).toBe(1);
        });
        it('should get sheet skills', () => {
            const skills = sheet.getSkills();
            const total = skills[SkillName_1.SkillName.fight].getModifiersTotal();
            expect(total).toBe(2);
        });
        describe('Devout', () => {
            let devoutSheet;
            beforeAll(() => {
                sheetBuilder.addDevotion(new Devotion_1.Devotion(Deities_1.Deities.get(DeityName_1.DeityName.linwuh), [
                    new EmptyMind_1.EmptyMind(),
                ]));
                devoutSheet = sheetBuilder.build();
            });
            it('should be devout', () => {
                const devotion = devoutSheet.getSheetDevotion();
                expect(devotion.isDevout()).toBeTruthy();
            });
            it('should have granted power', () => {
                const powers = devoutSheet.getSheetPowers();
                expect(powers.getGrantedPowers().has(GrantedPowerName_1.GrantedPowerName.emptyMind)).toBeTruthy();
            });
            it('should have devotion deity', () => {
                const devotion = devoutSheet.getSheetDevotion();
                expect(devotion.getDeity().name).toBe(DeityName_1.DeityName.linwuh);
            });
            it('should not accept not allowed power', () => {
                const build = () => {
                    const linWuh = Deities_1.Deities.get(DeityName_1.DeityName.linwuh);
                    const devotion = new Devotion_1.Devotion(linWuh, [
                        new AnalyticMind_1.AnalyticMind(),
                    ]);
                    sheetBuilder.addDevotion(devotion);
                };
                expect(build).toThrow('NOT_ALLOWED_POWER');
            });
            it('should should accept only one power', () => {
                const build = () => {
                    const linWuh = Deities_1.Deities.get(DeityName_1.DeityName.linwuh);
                    const devotion = new Devotion_1.Devotion(linWuh, [
                        new EmptyMind_1.EmptyMind(),
                        new EmptyMind_1.EmptyMind(),
                    ]);
                    sheetBuilder.addDevotion(devotion);
                };
                expect(build).toThrow('INVALID_POWER_COUNT');
            });
            it('should not accept a deity that does not permit this race and role', () => {
                const build = () => {
                    const devotion = new Devotion_1.Devotion(Deities_1.Deities.get(DeityName_1.DeityName.lena), [
                        new EmptyMind_1.EmptyMind(),
                    ]);
                    sheetBuilder.addDevotion(devotion);
                };
                expect(build).toThrow('NOT_ALLOWED_TO_DEVOTE');
            });
        });
    });
    describe('Dwarf Arcanist', () => {
        let sheet;
        let role;
        let race;
        let sheetBuilder;
        let origin;
        beforeAll(() => {
            role = ArcanistBuider_1.ArcanistBuilder
                .chooseSkills([[SkillName_1.SkillName.knowledge, SkillName_1.SkillName.diplomacy]])
                .choosePath(new ArcanistPathMage_1.ArcanistPathMage(new FlamesExplosion_1.FlamesExplosion()))
                .chooseSpells([new ArcaneArmor_1.ArcaneArmor(), new IllusoryDisguise_1.IllusoryDisguise(), new MentalDagger_1.MentalDagger()]);
            race = new Dwarf_1.Dwarf();
            sheetBuilder = new SheetBuilder_1.SheetBuilder();
            origin = new AnimalsFriend_1.AnimalsFriend([new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.animalHandling), new OriginBenefitOriginPower_1.OriginBenefitOriginPower(new SpecialFriend_1.SpecialFriend(SkillName_1.SkillName.religion))], EquipmentName_1.EquipmentName.horse);
            sheet = sheetBuilder
                .setInitialAttributes({ charisma: 0, constitution: 0, dexterity: 0, intelligence: 2, strength: 0, wisdom: 0 })
                .chooseRace(race)
                .chooseRole(role)
                .chooseOrigin(origin)
                .trainIntelligenceSkills([SkillName_1.SkillName.initiative, SkillName_1.SkillName.athletics])
                .addInitialEquipment({
                simpleWeapon: new Dagger_1.Dagger(),
                money: 20,
                armor: new LeatherArmor_1.LeatherArmor(),
            })
                .build();
        });
        it('should choose race', () => {
            expect(sheet.getSheetRace().getRace()).toBe(race);
        });
        it('should have displacement 9', () => {
            expect(sheet.getSheetDisplacement().getDisplacement()).toBe(6);
        });
        it('should have dark vision', () => {
            expect(sheet.getSheetVision().getVision()).toBe(Vision_1.Vision.dark);
        });
        it('should choose class', () => {
            expect(sheet.getSheetRole().getRole()).toBe(role);
        });
        it('should have initial role life points + constitution', () => {
            expect(sheet.getMaxLifePoints()).toBe(13);
        });
        it('should have role skills trained', () => {
            const skills = sheet.getSheetSkills().getSkills();
            expect(skills.mysticism.getIsTrained()).toBeTruthy();
            expect(skills.will.getIsTrained()).toBeTruthy();
            expect(skills.knowledge.getIsTrained()).toBeTruthy();
            expect(skills.diplomacy.getIsTrained()).toBeTruthy();
        });
        it('should have basic proficiencies', () => {
            expect(sheet.getSheetProficiencies().getProficiencies()).toContain(Proficiency_1.Proficiency.simple);
            expect(sheet.getSheetProficiencies().getProficiencies()).toContain(Proficiency_1.Proficiency.lightArmor);
        });
    });
    describe('Human Warrior - Missing fight skill for one weapon style', () => {
        it('should throw UNFILLED_POWER_REQUIREMENTS error', () => {
            const choices = [
                new VersatileChoiceSkill_1.VersatileChoiceSkill(SkillName_1.SkillName.acrobatics),
                new VersatileChoicePower_1.VersatileChoicePower(new Power_1.OneWeaponStyle()),
            ];
            const race = new Human_1.Human(['charisma', 'constitution', 'dexterity'], choices);
            const role = new Warrior_1.Warrior([[SkillName_1.SkillName.aim], [SkillName_1.SkillName.intimidation, SkillName_1.SkillName.athletics]]);
            const sheetBuilder = new SheetBuilder_1.SheetBuilder();
            const origin = new Acolyte_1.Acolyte([new OriginBenefitGeneralPower_1.OriginBenefitGeneralPower(new IronWill_1.IronWill()), new OriginBenefitSkill_1.OriginBenefitSkill(SkillName_1.SkillName.cure)]);
            expect(() => {
                sheetBuilder
                    .setInitialAttributes({ strength: 0, dexterity: 0, charisma: 0, constitution: 0, intelligence: 0, wisdom: 2 })
                    .chooseRace(race)
                    .chooseRole(role)
                    .chooseOrigin(origin)
                    .trainIntelligenceSkills([])
                    .addInitialEquipment({
                    simpleWeapon: new Dagger_1.Dagger(),
                    armor: new LeatherArmor_1.LeatherArmor(),
                    martialWeapon: new LongSword_1.LongSword(),
                    money: 24,
                })
                    .build();
            }).toThrow('Requisito não preenchido: Treinado em Luta');
        });
    });
});
