"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathSorcerer = void 0;
const AbilityEffects_1 = require("../../../../Ability/AbilityEffects");
const ArcanistPath_1 = require("../ArcanistPath");
class ArcanistPathSorcerer extends ArcanistPath_1.ArcanistPath {
    constructor(lineage) {
        super();
        this.lineage = lineage;
        this.pathName = ArcanistPath_1.ArcanistPathName.sorcerer;
        this.spellsAttribute = 'charisma';
        this.spellLearnFrequency = 'odd';
        this.effects = new AbilityEffects_1.AbilityEffects(lineage.effects.basic);
    }
    serializePath() {
        return {
            name: this.pathName,
            lineage: this.lineage.serialize(),
        };
    }
}
exports.ArcanistPathSorcerer = ArcanistPathSorcerer;
