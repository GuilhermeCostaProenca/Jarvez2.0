import { Modifiers } from '../Modifier/Modifiers';
type CharacterAttackModifiersConstructorParams = {
    test?: Modifiers;
    damage?: Modifiers;
};
export declare class CharacterAttackModifiers {
    readonly test: Modifiers;
    readonly damage: Modifiers;
    constructor(params?: CharacterAttackModifiersConstructorParams);
}
export {};
