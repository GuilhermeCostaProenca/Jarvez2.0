"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageDraconic = void 0;
const AbilityEffects_1 = require("../../../../../../Ability/AbilityEffects");
const ArcanistLineage_1 = require("../ArcanistLineage");
const ArcanistLineageType_1 = require("../ArcanistLineageType");
const ArcanistLineageDraconicCharismaBonusEffect_1 = require("./ArcanistLineageDraconicCharismaBonusEffect");
const ArcanistLineageDraconicDamageReductionEffect_1 = require("./ArcanistLineageDraconicDamageReductionEffect");
class ArcanistLineageDraconic extends ArcanistLineage_1.ArcanistLineage {
    constructor(damageType) {
        const damageReductionEffect = new ArcanistLineageDraconicDamageReductionEffect_1.ArcanistLineageDraconicDamageReductionEffect(damageType);
        const charismaBonusEffect = new ArcanistLineageDraconicCharismaBonusEffect_1.ArcanistLineageDraconicCharismaBonusEffect();
        super();
        this.type = ArcanistLineageType_1.ArcanistLineageType.draconic;
        this.effects = {
            basic: new AbilityEffects_1.AbilityEffects({
                passive: {
                    charismaBonus: charismaBonusEffect,
                    damageReduction: damageReductionEffect,
                },
            }),
            enhanced: new AbilityEffects_1.AbilityEffects(),
            higher: new AbilityEffects_1.AbilityEffects(),
        };
    }
    getDamageType() {
        return this.effects.basic.passive.damageReduction.damageType;
    }
    serialize() {
        return {
            type: this.type,
            damageType: this.getDamageType(),
        };
    }
}
exports.ArcanistLineageDraconic = ArcanistLineageDraconic;
