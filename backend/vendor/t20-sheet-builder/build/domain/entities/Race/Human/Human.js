"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Human = void 0;
const SelectableAttributesRace_1 = require("../../SelectableAttributesRace");
const RaceName_1 = require("../RaceName");
const Versatile_1 = require("./Versatile/Versatile");
class Human extends SelectableAttributesRace_1.SelectableAttributesRace {
    /**
 * Returns an instance of Human race.
 * @param selectedAttributes - 3 different attributes
 * @param versatileChoices - 2 skills or 1 skill and 1 general power
  **/
    constructor(selectedAttributes, versatileChoices = []) {
        super(selectedAttributes, RaceName_1.RaceName.human);
        this.abilities = {
            versatile: new Versatile_1.Versatile(),
        };
        versatileChoices.forEach(choice => {
            this.abilities.versatile.addChoice(choice);
        });
    }
    addVersatilChoice(choice) {
        this.abilities.versatile.addChoice(choice);
    }
    serializeSpecific() {
        return {
            name: Human.raceName,
            selectedAttributes: this.selectedAttributes,
            versatileChoices: this.abilities.versatile.effects.passive.default.choices
                .map(choice => choice.serialize()),
        };
    }
    get restrictedAttributes() {
        return [];
    }
    get fixedModifier() {
        return 1;
    }
    get selectableQuantity() {
        return 3;
    }
    get versatileChoices() {
        return this.abilities.versatile.effects.passive.default.choices;
    }
}
exports.Human = Human;
Human.raceName = RaceName_1.RaceName.human;
Human.attributeModifiers = {};
