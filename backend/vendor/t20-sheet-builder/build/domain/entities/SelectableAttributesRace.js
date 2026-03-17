"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SelectableAttributesRace = void 0;
const errors_1 = require("../errors");
const Race_1 = require("./Race/Race");
class SelectableAttributesRace extends Race_1.Race {
    constructor(selectedAttributes, name, initialAttributeModifiers) {
        super(name);
        this.selectedAttributes = selectedAttributes;
        this.attributeModifiers = {};
        this.validateSelectedAttributes(selectedAttributes);
        if (initialAttributeModifiers) {
            this.attributeModifiers = initialAttributeModifiers;
        }
        selectedAttributes.forEach(attribute => {
            this.attributeModifiers[attribute] = this.fixedModifier;
        });
    }
    validateSelectedAttributes(attributes) {
        if (attributes.length !== this.selectableQuantity) {
            throw new errors_1.SheetBuilderError('INVALID_ATTRIBUTES_SELECTION');
        }
        const isSomeAttributeRepeated = attributes
            .some((selectedAttribute, index) => attributes.indexOf(selectedAttribute) !== index);
        if (isSomeAttributeRepeated) {
            throw new errors_1.SheetBuilderError('INVALID_ATTRIBUTES_SELECTION');
        }
        const isSomeSelectedAttributeRestricted = attributes
            .some(selectedAttribute => this.restrictedAttributes.includes(selectedAttribute));
        if (isSomeSelectedAttributeRestricted) {
            throw new errors_1.SheetBuilderError('RESTRICTED_ATTRIBUTE');
        }
    }
}
exports.SelectableAttributesRace = SelectableAttributesRace;
