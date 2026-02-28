"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Level_1 = require("../../Sheet/Level");
const FixedModifier_1 = require("../../Modifier/FixedModifier/FixedModifier");
const PerLevelModifier_1 = require("../../Modifier/PerLevelModifier/PerLevelModifier");
const RaceAbilityName_1 = require("../../Race/RaceAbilityName");
const RoleName_1 = require("../../Role/RoleName");
const PointsMaxCalculatorFactory_1 = require("../PointsMaxCalculatorFactory");
const LifePoints_1 = require("./LifePoints");
describe('LifePoints', () => {
    it('should calculate max', () => {
        const lifePoints = new LifePoints_1.LifePoints();
        lifePoints.fixedModifiers.add(new FixedModifier_1.FixedModifier(RoleName_1.RoleName.arcanist, 8, new Set(['constitution'])));
        lifePoints.fixedModifiers.add(new FixedModifier_1.FixedModifier(RaceAbilityName_1.RaceAbilityName.hardAsRock, 3));
        lifePoints.perLevelModifiers.add(new PerLevelModifier_1.PerLevelModifier({
            source: RaceAbilityName_1.RaceAbilityName.hardAsRock,
            value: 1,
            includeFirstLevel: false,
        }));
        lifePoints.perLevelModifiers.add(new PerLevelModifier_1.PerLevelModifier({
            source: RoleName_1.RoleName.arcanist,
            value: 2,
            includeFirstLevel: false,
            attributeBonuses: new Set(['constitution']),
        }));
        const attributes = { charisma: 0, constitution: 2, dexterity: 0, intelligence: 0, strength: 0, wisdom: 0 };
        const maxCalculator = PointsMaxCalculatorFactory_1.PointsMaxCalculatorFactory.make(attributes, Level_1.Level.three);
        expect(lifePoints.getMax(maxCalculator)).toBe(23);
    });
});
