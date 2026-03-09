import { type ArcanisPathWizardFocusName, type ArcanistLineageDraconicDamageType, type ArcanistLineageType, type Attribute, type GeneralPowerName, type SerializedRole, type SkillName } from '../..';
import { type SpellName } from '../../Spell';
import { type Arcanist } from './Arcanist';
import { type ArcanistPathName } from './ArcanistPath';
import { type SerializedArcanist, type SerializedArcanistPath } from './SerializedArcanist';
export type ArcanistFactoryParams = {
    chosenSkills: SkillName[][];
    initialSpells: SpellName[];
    path: ArcanistPathName;
    mageSpell?: SpellName;
    wizardFocus?: ArcanisPathWizardFocusName;
    sorcererLineage?: ArcanistLineageType;
    sorcererLineageDraconicDamageType?: ArcanistLineageDraconicDamageType;
    sorcererLineageFaerieExtraSpell?: SpellName;
    sorcererLineageRedExtraPower?: GeneralPowerName;
    sorcererLineageRedAttribute?: Attribute;
};
export declare class ArcanistFactory {
    static makeFromParams(params: ArcanistFactoryParams): Arcanist;
    static makeFromSerialized<P extends SerializedArcanistPath>(serialized: SerializedRole<SerializedArcanist<P>>): Arcanist;
}
