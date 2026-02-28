import type { Attributes } from './Sheet/Attributes';
export declare class StringHelper {
    static capitalize(string: string): string;
    static addNumberSign(number: number): string;
    static getAttributesText(attributes: Partial<Attributes>): string;
}
