"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageRed = void 0;
const AbilityEffects_1 = require("../../../../../../Ability/AbilityEffects");
const ArcanistLineage_1 = require("../ArcanistLineage");
const ArcanistLineageType_1 = require("../ArcanistLineageType");
const ArcanistLineageRedCustomTormentaPowersAttributeEffect_1 = require("./ArcanistLineageRedCustomTormentaPowersAttributeEffect");
const ArcanistLineageRedExtraTormentaPowerEffect_1 = require("./ArcanistLineageRedExtraTormentaPowerEffect");
class ArcanistLineageRed extends ArcanistLineage_1.ArcanistLineage {
    constructor(power, attributeToLose = 'charisma') {
        super();
        this.attributeToLose = attributeToLose;
        this.type = ArcanistLineageType_1.ArcanistLineageType.red;
        this.effects = {
            basic: new AbilityEffects_1.AbilityEffects({
                passive: {
                    customTormentaPowersAttribute: new ArcanistLineageRedCustomTormentaPowersAttributeEffect_1.ArcanistLineageRedCustomTormentaPowersAttributeEffect(attributeToLose),
                    extraTormentaPower: new ArcanistLineageRedExtraTormentaPowerEffect_1.ArcanistLineageRedExtraTormentaPowerEffect(power),
                },
            }),
            enhanced: new AbilityEffects_1.AbilityEffects(),
            higher: new AbilityEffects_1.AbilityEffects(),
        };
    }
    getExtraPower() {
        return this.effects.basic.passive.extraTormentaPower.power;
    }
    getCustomTormentaPowersAttribute() {
        return this.effects.basic.passive.customTormentaPowersAttribute.attribute;
    }
    serialize() {
        return {
            type: this.type,
            extraPower: this.getExtraPower().name,
            customTormentaAttribute: this.getCustomTormentaPowersAttribute(),
        };
    }
}
exports.ArcanistLineageRed = ArcanistLineageRed;
