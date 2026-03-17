import { type TransactionInterface } from '../../../Sheet/TransactionInterface';
import type { SkillName } from '../../../Skill/SkillName';
import type { TranslatableName } from '../../../Translator';
import { type SerializedVersatileChoiceSkill } from '../../SerializedRace';
import { VersatileChoice } from './VersatileChoice';
export declare class VersatileChoiceSkill extends VersatileChoice {
    readonly skill: SkillName;
    constructor(skill: SkillName);
    addToSheet(transaction: TransactionInterface, source: TranslatableName): void;
    serialize(): SerializedVersatileChoiceSkill;
}
