"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetAttributes = void 0;
class SheetAttributes {
    static get initial() {
        return {
            charisma: 0,
            constitution: 0,
            dexterity: 0,
            intelligence: 0,
            strength: 0,
            wisdom: 0,
        };
    }
    static makeFromSerialized(serialized) {
        const attributes = new SheetAttributes(SheetAttributes.initial, serialized.tormentaPowersAttribute);
        attributes.setInitialAttributes(serialized.initialAttributes);
        return attributes;
    }
    constructor(attributes = SheetAttributes.initial, tormentaPowersAttribute = 'charisma') {
        this.attributes = attributes;
        this.tormentaPowersAttribute = tormentaPowersAttribute;
    }
    setInitialAttributes(attributes) {
        this.attributes = attributes;
        this.initialAttributes = attributes;
    }
    getInitialAttributes() {
        var _a;
        return (_a = this.initialAttributes) !== null && _a !== void 0 ? _a : SheetAttributes.initial;
    }
    applyRaceModifiers(modifiers) {
        const updatedAttributes = {};
        Object.entries(modifiers).forEach(([key, modifier]) => {
            const attribute = key;
            updatedAttributes[attribute] = this.attributes[attribute] + modifier;
        });
        this.attributes = Object.assign(Object.assign({}, this.attributes), updatedAttributes);
    }
    changeTormentaPowersAttribute(attribute) {
        this.tormentaPowersAttribute = attribute;
    }
    decreaseAttribute(attribute, quantity) {
        this.attributes[attribute] -= quantity;
    }
    increaseAttribute(attribute, quantity) {
        this.attributes[attribute] += quantity;
    }
    getTormentaPowersAttribute() {
        return this.tormentaPowersAttribute;
    }
    getValues() {
        return this.attributes;
    }
}
exports.SheetAttributes = SheetAttributes;
