"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Race = void 0;
const ApplyRaceAbility_1 = require("../Action/ApplyRaceAbility");
const ApplyRaceModifiers_1 = require("../Action/ApplyRaceModifiers");
class Race {
    static serialize(race) {
        return {
            name: race.name,
            abilities: Object.values(race.abilities).map(ability => ability.serialize()),
            attributeModifiers: race.attributeModifiers,
        };
    }
    constructor(name) {
        this.name = name;
    }
    addToSheet(transaction) {
        this.applyAttributesModifiers(transaction);
        this.applyAbilities(transaction);
    }
    serialize() {
        return Object.assign(Object.assign({}, Race.serialize(this)), this.serializeSpecific());
    }
    applyAttributesModifiers(transaction) {
        transaction.run(new ApplyRaceModifiers_1.ApplyRaceModifiers({
            payload: {
                modifiers: this.attributeModifiers,
            },
            transaction,
        }));
    }
    applyAbilities(transaction) {
        Object.values(this.abilities).forEach(ability => {
            transaction.run(new ApplyRaceAbility_1.ApplyRaceAbility({
                payload: {
                    ability,
                    source: this.name,
                },
                transaction,
            }));
        });
    }
}
exports.Race = Race;
