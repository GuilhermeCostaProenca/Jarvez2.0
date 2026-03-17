"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Lefeu = void 0;
const errors_1 = require("../../../errors");
const SelectableAttributesRace_1 = require("../../SelectableAttributesRace");
const RaceName_1 = require("../RaceName");
const Deformity_1 = require("./Deformity/Deformity");
const SonOfTormenta_1 = require("./SonOfTormenta/SonOfTormenta");
class Lefeu extends SelectableAttributesRace_1.SelectableAttributesRace {
    /**
 * Returns an instance of lefeu race.
 * @param selectedAttributes - 3 different attributes
 * @param deformity - +2 on 2 skills
  **/
    constructor(selectedAttributes) {
        if (selectedAttributes.find(attribute => attribute === 'charisma')) {
            throw new errors_1.SheetBuilderError('INVALID_ATTRIBUTES_SELECTION');
        }
        super(selectedAttributes, RaceName_1.RaceName.lefeu, {
            charisma: -1,
        });
        this.abilities = {
            sonOfTormenta: new SonOfTormenta_1.SonOfTormenta(),
            deformity: new Deformity_1.Deformity(),
        };
        this.previousRace = RaceName_1.RaceName.human;
    }
    addDeformities(skills) {
        skills.forEach(skill => {
            this.abilities.deformity.addDeformity(skill);
        });
    }
    setPreviousRace(previousRace) {
        this.previousRace = previousRace;
    }
    getPreviousRace() {
        return this.previousRace;
    }
    serializeSpecific() {
        return {
            name: Lefeu.raceName,
            selectedAttributes: this.selectedAttributes,
            previousRace: this.previousRace,
            deformityChoices: this.abilities.deformity.serializeChoices(),
        };
    }
    get restrictedAttributes() {
        return ['charisma'];
    }
    get fixedModifier() {
        return 1;
    }
    get selectableQuantity() {
        return 3;
    }
}
exports.Lefeu = Lefeu;
Lefeu.raceName = RaceName_1.RaceName.lefeu;
Lefeu.attributeModifiers = {};
