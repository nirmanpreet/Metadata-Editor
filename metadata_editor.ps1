
Add-Type -AssemblyName PresentationCore, PresentationFramework

function New-Window {
    param (
        [string]$Title,
        [int]$Width = 400,
        [int]$Height = 300
    )
    $window = New-Object System.Windows.Window
    $window.Title = $Title
    $window.Width = $Width
    $window.Height = $Height
    $window.WindowStartupLocation = "CenterScreen"
    $window.ResizeMode = "NoResize"
    return $window
}

function Select-File {
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Filter = "All Files (*.*)|*.*"
    $dialog.Title = "Select a File to Edit Metadata"
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $dialog.FileName
    }
    return $null
}

function Display-Metadata {
    param ([string]$Path)
    $file = Get-Item $Path
    [PSCustomObject]@{
        "Created"      = $file.CreationTime
        "Last Accessed" = $file.LastAccessTime
        "Last Modified" = $file.LastWriteTime
    }
}

function Edit-Metadata {
    param (
        [string]$Path,
        [string]$PropertyName
    )

    $window = New-Window -Title "Edit $PropertyName" -Width 350 -Height 200
    $stackPanel = New-Object System.Windows.Controls.StackPanel

    $label = New-Object System.Windows.Controls.Label
    $label.Content = "Enter new $PropertyName (yyyy-MM-dd HH:mm:ss):"
    $stackPanel.Children.Add($label)

    $textBox = New-Object System.Windows.Controls.TextBox
    $textBox.Margin = "10"
    $stackPanel.Children.Add($textBox)

    $okButton = New-Object System.Windows.Controls.Button
    $okButton.Content = "OK"
    $okButton.Margin = "10"
    $okButton.Add_Click({
        try {
            $newDate = [datetime]::ParseExact($textBox.Text, "yyyy-MM-dd HH:mm:ss", $null)
            $file = Get-Item -Path $Path
            $file."$PropertyName" = $newDate
            [System.Windows.MessageBox]::Show("$PropertyName updated successfully!", "Success")
            $window.Close()
        } catch {
            [System.Windows.MessageBox]::Show("Invalid date format. Try again.", "Error")
        }
    })
    $stackPanel.Children.Add($okButton)

    $window.Content = $stackPanel
    $window.ShowDialog()
}

function Show-MetadataEditor {
    $filePath = Select-File
    if (-not $filePath) {
        [System.Windows.MessageBox]::Show("No file selected. Exiting.", "Info")
        return
    }

    $window = New-Window -Title "File Metadata Editor"
    $stackPanel = New-Object System.Windows.Controls.StackPanel

    $label = New-Object System.Windows.Controls.Label
    $label.Content = "File: $filePath"
    $label.Margin = "10"
    $stackPanel.Children.Add($label)

    $metadata = Display-Metadata -Path $filePath
    $metadata.GetEnumerator() | ForEach-Object {
        $propertyLabel = New-Object System.Windows.Controls.Label
        $propertyLabel.Content = "$($_.Key): $($_.Value)"
        $propertyLabel.Margin = "5"
        $stackPanel.Children.Add($propertyLabel)

        $editButton = New-Object System.Windows.Controls.Button
        $editButton.Content = "Edit $($_.Key)"
        $editButton.Margin = "5"
        $editButton.Add_Click({
            Edit-Metadata -Path $filePath -PropertyName $_.Key
        })
        $stackPanel.Children.Add($editButton)
    }

    $closeButton = New-Object System.Windows.Controls.Button
    $closeButton.Content = "Close"
    $closeButton.Margin = "10"
    $closeButton.Add_Click({ $window.Close() })
    $stackPanel.Children.Add($closeButton)

    $window.Content = $stackPanel
    $window.ShowDialog()
}

# Run the Metadata Editor
Show-MetadataEditor
