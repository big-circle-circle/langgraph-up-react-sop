"""Utility & helper functions."""

from typing import Optional, Union
import pandas as pd
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_qwq import ChatQwen, ChatQwQ


def merge_two_tables(filename1, filename2, output_filename, on_columns):
    """Merge two CSV tables on specified columns and save to output file. columns with same name in both files will be merged.

    Args:
        filename1: Path to the first CSV file.
        filename2: Path to the second CSV file.
        output_filename: Path to save the merged CSV file.
        on_columns: List of column names to merge on.
    """
    import pandas as pd

    df1 = pd.read_csv(filename1)
    df2 = pd.read_csv(filename2)


    # Merge with default suffixes to keep all columns first
    merged_df = pd.merge(df1, df2, on=on_columns, how='outer', suffixes=('_1', '_2'))

    # Find columns that have suffixes (overlapped columns)
    cols_1 = [col for col in merged_df.columns if col.endswith('_1')]
    for col_1 in cols_1:
        base_col = col_1[:-2]  # original column name without suffix
        col_2 = base_col + '_2'
        if col_2 in merged_df.columns:
            # Consolidate two columns: prefer _1, else _2
            merged_df[base_col] = merged_df[col_1].combine_first(merged_df[col_2])
            # Drop the suffixed columns
            merged_df.drop([col_1, col_2], axis=1, inplace=True)
        else:
            # If _2 version doesn't exist, just rename _1 column to original
            merged_df.rename(columns={col_1: base_col}, inplace=True)

    # Columns without suffixes remain untouched, including on_columns
    merged_df.to_csv(output_filename, index=False)

def generate_prompt_for_aircraft_id(aircraft_id: str, filename) -> str:
    """Generate a prompt to retrive the data record with aircraft_id, and convert the data record to markdown table.    

    Args:
        aircraft_id: The ID of the aircraft to verify.

    Returns:
        A formatted prompt string.
    """

    df = pd.read_csv(filename)
    record = df[df['aircraft_id'] == aircraft_id]

    if record.empty:
        return f"No record found for aircraft_id: {aircraft_id}, please check the aircraft_id and try again, e,g., make generate_prompt AIRCRAFT_ID=a_00123"

    # Convert the record to a markdown table
    markdown_table = record.to_markdown(index=False)

    prompt = f"\n===========Copy the prompts below===================\n\nAnalyze the below data record and execute (call) the tool functions according to the sop.  {aircraft_id}:\n\n{markdown_table}\n\n ==========End of prompt==================\n"
    return prompt


def normalize_region(region: str) -> Optional[str]:
    """Normalize region aliases to standard values.

    Args:
        region: Region string to normalize

    Returns:
        Normalized region ('prc' or 'international') or None if invalid
    """
    if not region:
        return None

    region_lower = region.lower()
    if region_lower in ("prc", "cn"):
        return "prc"
    elif region_lower in ("international", "en"):
        return "international"
    return None


def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def load_chat_model(
    fully_specified_name: str,
) -> Union[BaseChatModel, ChatQwQ, ChatQwen]:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider:model'.
    """
    provider, model = fully_specified_name.split(":", maxsplit=1)
    provider_lower = provider.lower()

    # Handle Qwen models specially with dashscope integration
    if provider_lower == "qwen":
        from .models import create_qwen_model

        return create_qwen_model(model)

    # Handle SiliconFlow models
    if provider_lower == "siliconflow":
        from .models import create_siliconflow_model

        return create_siliconflow_model(model)

    # Use standard langchain initialization for other providers
    return init_chat_model(model, model_provider=provider)
