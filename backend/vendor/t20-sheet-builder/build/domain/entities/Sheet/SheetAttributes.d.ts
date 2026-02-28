import { type Attribute, type Attributes } from './Attributes';
import { type SerializedSheetInterface } from './SerializedSheet';
import { type SheetAttributesInterface } from './SheetAttributesInterface';
export declare class SheetAttributes implements SheetAttributesInterface {
    private attributes;
    private tormentaPowersAttribute;
    static get initial(): Attributes;
    static makeFromSerialized(serialized: SerializedSheetInterface): SheetAttributes;
    private initialAttributes;
    constructor(attributes?: Attributes, tormentaPowersAttribute?: Attribute);
    setInitialAttributes(attributes: Attributes): void;
    getInitialAttributes(): Attributes;
    applyRaceModifiers(modifiers: Partial<Attributes>): void;
    changeTormentaPowersAttribute(attribute: keyof Attributes): void;
    decreaseAttribute(attribute: keyof Attributes, quantity: number): void;
    increaseAttribute(attribute: keyof Attributes, quantity: number): void;
    getTormentaPowersAttribute(): keyof Attributes;
    getValues(): Attributes;
}
