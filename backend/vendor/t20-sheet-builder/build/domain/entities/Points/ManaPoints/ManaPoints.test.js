"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Level_1 = require("../../Sheet/Level");
const FixedModifier_1 = require("../../Modifier/FixedModifier/FixedModifier");
const FixedModifiersListTotalCalculator_1 = require("../../Modifier/FixedModifier/FixedModifiersListTotalCalculator");
const PerLevelModifier_1 = require("../../Modifier/PerLevelModifier/PerLevelModifier");
const PerLevelModifiersListTotalCalculator_1 = require("../../Modifier/PerLevelModifier/PerLevelModifiersListTotalCalculator");
const RaceAbilityName_1 = require("../../Race/RaceAbilityName");
const RoleName_1 = require("../../Role/RoleName");
const PointsMaxCalculator_1 = require("../PointsMaxCalculator");
const ManaPoints_1 = require("./ManaPoints");
describe('ManaPoints', () => {
    it('should calculate max on level one', () => {
        const manaPoints = new ManaPoints_1.ManaPoints();
        manaPoints.fixedModifiers.add(new FixedModifier_1.FixedModifier(RoleName_1.RoleName.arcanist, 8, new Set(['constitution'])));
        manaPoints.fixedModifiers.add(new FixedModifier_1.FixedModifier(RaceAbilityName_1.RaceAbilityName.hardAsRock, 3));
        manaPoints.perLevelModifiers.add(new PerLevelModifier_1.PerLevelModifier({
            source: RaceAbilityName_1.RaceAbilityName.hardAsRock,
            value: 1,
            includeFirstLevel: false,
        }));
        manaPoints.perLevelModifiers.add(new PerLevelModifier_1.PerLevelModifier({
            source: RoleName_1.RoleName.arcanist,
            value: 2,
            includeFirstLevel: false,
            attributeBonuses: new Set(['constitution']),
        }));
        const attributes = { charisma: 0, constitution: 2, dexterity: 0, intelligence: 0, strength: 0, wisdom: 0 };
        const fixedCalculator = new FixedModifiersListTotalCalculator_1.FixedModifiersListTotalCalculator(attributes);
        const perLevelCalculator = new PerLevelModifiersListTotalCalculator_1.PerLevelModifiersListTotalCalculator(attributes, Level_1.Level.three);
        const maxCalculator = new PointsMaxCalculator_1.PointsMaxCalculator(fixedCalculator, perLevelCalculator);
        expect(manaPoints.getMax(maxCalculator)).toBe(23);
    });
});
