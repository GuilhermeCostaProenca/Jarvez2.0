"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const __1 = require("../..");
describe('Arcanist Factory', () => {
    it('should create sorcerer', () => {
        const sorcerer = __1.ArcanistFactory.makeFromParams({
            chosenSkills: [[__1.SkillName.knowledge, __1.SkillName.diplomacy]],
            path: __1.ArcanistPathName.sorcerer,
            sorcererLineage: __1.ArcanistLineageType.draconic,
            sorcererLineageDraconicDamageType: __1.DamageType.acid,
            initialSpells: [__1.SpellName.arcaneArmor, __1.SpellName.flamesExplosion, __1.SpellName.illusoryDisguise],
        });
        expect(sorcerer).toBeDefined();
    });
});
