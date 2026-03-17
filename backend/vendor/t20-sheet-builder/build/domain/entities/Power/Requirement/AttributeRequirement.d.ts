import type { Attribute } from '../../Sheet/Attributes';
import type { SheetInterface } from '../../Sheet/SheetInterface';
import { Requirement } from './Requirement';
export declare class AttributeRequirement extends Requirement {
    readonly attribute: Attribute;
    readonly value: number;
    readonly description: string;
    constructor(attribute: Attribute, value: number);
    verify(sheet: SheetInterface): boolean;
    protected getDescription(): string;
}
