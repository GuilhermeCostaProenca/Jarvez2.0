import { type TranslatableName } from './Translator';
export declare class Translatable {
    readonly value: TranslatableName;
    constructor(value: TranslatableName);
    getTranslation(): string;
}
