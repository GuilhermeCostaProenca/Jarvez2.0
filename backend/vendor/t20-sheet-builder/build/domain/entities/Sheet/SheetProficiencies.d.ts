import { Proficiency } from './Proficiency';
import { type SheetProficienciesInterface } from './SheetProficienciesInterface';
export declare class SheetProficiencies implements SheetProficienciesInterface {
    private readonly proficiencies;
    constructor(proficiencies?: Set<Proficiency>);
    addProficiency(proficiency: Proficiency): void;
    has(proficiency: Proficiency): boolean;
    getProficiencies(): Proficiency[];
}
